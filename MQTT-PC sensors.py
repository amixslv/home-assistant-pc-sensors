import psutil
import paho.mqtt.client as mqtt
import time
import socket
import platform
import json
import wmi

# MQTT configuration
MQTT_BROKER = "192.168.xx.xx" # Your Home Assistant IP adress
MQTT_PORT = 1883
MQTT_TOPIC_PREFIX = "home/laptop"
MQTT_USER = "Your username" # Change this to your own
MQTT_PASS = "Your strong password" # Change this to your own

UPDATE_INTERVAL = 600  # 10 minūtes# 10 minutes (Time must be in seconds). Can be changed to any other time
CHECK_INTERVAL = 10    # How often to check charging status (Time is shown in seconds)

client = mqtt.Client()
client.username_pw_set(MQTT_USER, MQTT_PASS)
client.connect(MQTT_BROKER, MQTT_PORT, 60)
client.loop_start()

hostname = socket.gethostname()
discovery_prefix = "homeassistant"
prev_values = {}

# Gets the manufacturer and model from the computer
def get_system_info():
    try:
        c = wmi.WMI()
        system = c.Win32_ComputerSystem()[0]
        return system.Manufacturer, system.Model
    except:
        return "Unknown", "Unknown"

manufacturer, model = get_system_info()

# Sensors we will register
sensor_definitions = {
    "battery_percent": {"name": "Battery", "unit": "%", "device_class": "battery"},
    "charging": {"name": "Charging", "icon": "mdi:battery-charging"},
    "cpu_percent": {"name": "CPU", "unit": "%", "device_class": "power_factor"},
    "ram_percent": {"name": "RAM", "unit": "%"},
    "disk_percent": {"name": "Disk", "unit": "%"},
    "net_sent_mb": {"name": "Net Sent", "unit": "MB"},
    "net_recv_mb": {"name": "Net Received", "unit": "MB"},
    "uptime_minutes": {"name": "Uptime", "unit": "min"},
    "hostname": {"name": "Hostname"},
    "os": {"name": "OS"}
}

# Publishes sensor configuration in Home Assistant Discovery format
def publish_discovery_config():
    for key, props in sensor_definitions.items():
        config_topic = f"{discovery_prefix}/sensor/{hostname}_{key}/config"
        state_topic = f"{MQTT_TOPIC_PREFIX}/{hostname}/{key}"
        payload = {
            "name": props["name"],
            "state_topic": state_topic,
            "unique_id": f"{hostname}_{key}",
            "device": {
                "identifiers": [hostname],
                "name": hostname,
                "manufacturer": manufacturer,
                "model": model
            }
        }
        if "unit" in props:
            payload["unit_of_measurement"] = props["unit"]
        if "device_class" in props:
            payload["device_class"] = props["device_class"]
        if "icon" in props:
            payload["icon"] = props["icon"]

        client.publish(config_topic, json.dumps(payload), retain=True)

# Gets sensor data
def get_sensors():
    battery = psutil.sensors_battery()
    return {
        "battery_percent": battery.percent if battery else None,
        "charging": battery.power_plugged if battery else None,
        "cpu_percent": psutil.cpu_percent(interval=None),
        "ram_percent": psutil.virtual_memory().percent,
        "disk_percent": psutil.disk_usage('/').percent,
        "net_sent_mb": round(psutil.net_io_counters().bytes_sent / 1024 / 1024, 2),
        "net_recv_mb": round(psutil.net_io_counters().bytes_recv / 1024 / 1024, 2),
        "uptime_minutes": int(time.time() - psutil.boot_time()) // 60,
        "hostname": hostname,
        "os": platform.system()
    }

# Publish the sensor if the value has changed
def publish_if_changed(key, value):
    global prev_values
    if prev_values.get(key) != value:
        topic = f"{MQTT_TOPIC_PREFIX}/{hostname}/{key}"
        client.publish(topic, value)
        print(f"[CHANGED] {key} → {value}")
        prev_values[key] = value

# Publish the configuration once
publish_discovery_config()

# Main cycle
while True:
    sensors = get_sensors()
    for key, value in sensors.items():
        publish_if_changed(key, value)
    time.sleep(CHECK_INTERVAL)
