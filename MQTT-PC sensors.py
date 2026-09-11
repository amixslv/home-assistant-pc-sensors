import psutil
import paho.mqtt.client as mqtt
import time
import socket
import platform
import json
from pathlib import Path
import wmi

CONFIG_PATH = Path(__file__).with_name("config.json")


def load_configuration():
    try:
        with CONFIG_PATH.open(encoding="utf-8") as config_file:
            return json.load(config_file)
    except FileNotFoundError as error:
        raise RuntimeError(
            "config.json was not found. Copy config.example.json to "
            "config.json and enter your MQTT settings."
        ) from error
    except json.JSONDecodeError as error:
        raise RuntimeError(f"Invalid JSON in {CONFIG_PATH}: {error}") from error


config = load_configuration()
MQTT_BROKER = config.get("mqtt_broker", "")
MQTT_PORT = config.get("mqtt_port", 1883)
MQTT_TOPIC_PREFIX = config.get("mqtt_topic_prefix", "")
MQTT_USER = config.get("mqtt_user", "")
MQTT_PASS = config.get("mqtt_pass", "")

UPDATE_INTERVAL = config.get("UPDATE_INTERVAL", 60)
CHECK_INTERVAL = config.get("CHECK_INTERVAL", 10)

hostname = socket.gethostname()
discovery_prefix = "homeassistant"
prev_values = {}


def create_mqtt_client():
    if hasattr(mqtt, "CallbackAPIVersion"):
        client = mqtt.Client(
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2
        )
    else:
        client = mqtt.Client()

    if MQTT_USER:
        client.username_pw_set(MQTT_USER, MQTT_PASS)
    return client


def validate_configuration():
    if not MQTT_BROKER or MQTT_BROKER == "192.168.x.x":
        raise ValueError(
            "Set mqtt_broker in config.json."
        )
    if MQTT_USER and not MQTT_PASS:
        raise ValueError(
            "Set mqtt_pass in config.json, or leave mqtt_user empty for "
            "anonymous access."
        )


# Gets the manufacturer and model from the computer
def get_system_info():
    try:
        c = wmi.WMI()
        system = c.Win32_ComputerSystem()[0]
        return system.Manufacturer, system.Model
    except (IndexError, AttributeError, wmi.x_wmi):
        return "Unknown", "Unknown"


manufacturer, model = get_system_info()

# Sensors we will register
sensor_definitions = {
    # ============================
    # BATTERY
    # ============================
    "battery_percent": {"name": "Battery", "unit": "%", "device_class": "battery"},
    "charging": {"name": "Charging", "icon": "mdi:battery-charging"},
    
    # ============================
    # CPU
    # ============================
    "cpu_percent": {"name": "CPU Load", "unit": "%"},
    
    # ============================
    # GPU (praktiski noderīgie)
    # ============================
    
    # ============================
    # RAM
    # ============================
    "ram_percent": {"name": "RAM Load", "unit": "%"},

    # ============================
    # DISK
    # ============================
    "disk_percent": {"name": "Disk Usage", "unit": "%"},

    # ============================
    # NETWORK
    # ============================
    "net_sent_mb": {"name": "Net Sent", "unit": "MB"},
    "net_recv_mb": {"name": "Net Received", "unit": "MB"},
    
    # ============================
    # Wi-Fi
    # ============================
    
    # ============================
    # SYSTEM
    # ============================
    "uptime_minutes": {"name": "Uptime", "unit": "min"},
    "hostname": {"name": "Hostname"},
    "os": {"name": "OS"},

  
    
}


# Publishes sensor configuration in Home Assistant Discovery format
def publish_discovery_config(client):
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


def get_battery_sensors():
    battery = psutil.sensors_battery()
    return {
        "battery_percent": battery.percent if battery else None,
        "charging": battery.power_plugged if battery else None
    }


# Gets sensor data
def get_sensors():
    sensors = get_battery_sensors()
    sensors.update({
        "cpu_percent": psutil.cpu_percent(interval=None),
        "ram_percent": psutil.virtual_memory().percent,
        "disk_percent": psutil.disk_usage(Path.home().anchor).percent,
        "net_sent_mb": round(psutil.net_io_counters().bytes_sent / 1024 / 1024, 2),
        "net_recv_mb": round(psutil.net_io_counters().bytes_recv / 1024 / 1024, 2),
        "uptime_minutes": int(time.time() - psutil.boot_time()) // 60,
        "hostname": hostname,
        "os": platform.system(),
        
    })
    return sensors


# Publish the sensor if the value has changed
def publish_if_changed(client, key, value):
    if prev_values.get(key) != value:
        topic = f"{MQTT_TOPIC_PREFIX}/{hostname}/{key}"
        payload = json.dumps(value) if isinstance(value, bool) else value
        client.publish(topic, payload, retain=True)
        # Use ASCII output to avoid UnicodeEncodeError on Windows cp1252 consoles
        print(f"[CHANGED] {key} -> {value}")
        prev_values[key] = value


def publish_sensors(client, sensors):
    for key, value in sensors.items():
        publish_if_changed(client, key, value)


def main():
    validate_configuration()
    client = create_mqtt_client()
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_start()

    try:
        publish_discovery_config(client)
        publish_sensors(client, get_sensors())
        next_full_update = time.monotonic() + UPDATE_INTERVAL

        while True:
            time.sleep(CHECK_INTERVAL)
            if time.monotonic() >= next_full_update:
                publish_sensors(client, get_sensors())
                next_full_update = time.monotonic() + UPDATE_INTERVAL
            else:
                publish_sensors(client, get_battery_sensors())
    except KeyboardInterrupt:
        print("Stopping...")
    finally:
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    main()
