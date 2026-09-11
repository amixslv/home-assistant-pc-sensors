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
    "battery_percent": {"name": "Battery", "unit": "%", "device_class": "battery"},
    "charging": {"name": "Charging", "icon": "mdi:battery-charging"},
    "battery_time_remaining_minutes": {"name": "Battery Time Remaining", "unit": "min", "device_class": "duration"},
    "cpu_percent": {"name": "CPU", "unit": "%", "device_class": "power_factor"},
    "cpu_count_logical": {"name": "CPU Logical Cores"},
    "cpu_count_physical": {"name": "CPU Physical Cores"},
    "cpu_frequency_mhz": {"name": "CPU Frequency", "unit": "MHz", "device_class": "frequency"},
    "ram_percent": {"name": "RAM", "unit": "%"},
    "ram_total_gb": {"name": "RAM Total", "unit": "GB", "device_class": "data_size"},
    "ram_used_gb": {"name": "RAM Used", "unit": "GB", "device_class": "data_size"},
    "ram_available_gb": {"name": "RAM Available", "unit": "GB", "device_class": "data_size"},
    "swap_percent": {"name": "Swap", "unit": "%"},
    "swap_total_gb": {"name": "Swap Total", "unit": "GB", "device_class": "data_size"},
    "swap_used_gb": {"name": "Swap Used", "unit": "GB", "device_class": "data_size"},
    "disk_percent": {"name": "Disk", "unit": "%"},
    "disk_total_gb": {"name": "Disk Total", "unit": "GB", "device_class": "data_size"},
    "disk_used_gb": {"name": "Disk Used", "unit": "GB", "device_class": "data_size"},
    "disk_free_gb": {"name": "Disk Free", "unit": "GB", "device_class": "data_size"},
    "net_sent_mb": {"name": "Net Sent", "unit": "MB", "device_class": "data_size"},
    "net_recv_mb": {"name": "Net Received", "unit": "MB", "device_class": "data_size"},
    "net_packets_sent": {"name": "Net Packets Sent"},
    "net_packets_recv": {"name": "Net Packets Received"},
    "net_errors_in": {"name": "Net Errors In"},
    "net_errors_out": {"name": "Net Errors Out"},
    "net_drops_in": {"name": "Net Drops In"},
    "net_drops_out": {"name": "Net Drops Out"},
    "uptime_minutes": {"name": "Uptime", "unit": "min", "device_class": "duration"},
    "process_count": {"name": "Processes"},
    "logged_in_users": {"name": "Logged In Users"},
    "hostname": {"name": "Hostname"},
    "os": {"name": "OS"},
    "os_version": {"name": "OS Version"},
    "architecture": {"name": "Architecture"},
    "processor": {"name": "Processor"}
}

enabled_sensors = config.get("sensors", list(sensor_definitions))


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
    if not isinstance(enabled_sensors, list) or not all(
        isinstance(sensor, str) for sensor in enabled_sensors
    ):
        raise ValueError(
            "Set sensors in config.json to a list of sensor names."
        )

    unknown_sensors = sorted(set(enabled_sensors) - set(sensor_definitions))
    if unknown_sensors:
        available = ", ".join(sensor_definitions)
        unknown = ", ".join(unknown_sensors)
        raise ValueError(
            f"Unknown sensors in config.json: {unknown}. "
            f"Available sensors: {available}."
        )


# Publishes sensor configuration in Home Assistant Discovery format
def publish_discovery_config(client):
    for key, props in sensor_definitions.items():
        config_topic = f"{discovery_prefix}/sensor/{hostname}_{key}/config"
        if key not in enabled_sensors:
            client.publish(config_topic, "", retain=True)
            continue

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
        "charging": battery.power_plugged if battery else None,
        "battery_time_remaining_minutes": (
            battery.secsleft // 60
            if battery and battery.secsleft >= 0
            else None
        )
    }


def bytes_to_gb(value):
    return round(value / 1024 ** 3, 2)


# Gets sensor data
def get_sensors():
    memory = psutil.virtual_memory()
    swap = psutil.swap_memory()
    disk = psutil.disk_usage(Path.home().anchor)
    network = psutil.net_io_counters()
    cpu_frequency = psutil.cpu_freq()

    sensors = get_battery_sensors()
    sensors.update({
        "cpu_percent": psutil.cpu_percent(interval=None),
        "cpu_count_logical": psutil.cpu_count(logical=True),
        "cpu_count_physical": psutil.cpu_count(logical=False),
        "cpu_frequency_mhz": (round(cpu_frequency.current, 2) if cpu_frequency else None),
        "ram_percent": memory.percent,
        "ram_total_gb": bytes_to_gb(memory.total),
        "ram_used_gb": bytes_to_gb(memory.used),
        "ram_available_gb": bytes_to_gb(memory.available),
        "swap_percent": swap.percent,
        "swap_total_gb": bytes_to_gb(swap.total),
        "swap_used_gb": bytes_to_gb(swap.used),
        "disk_percent": disk.percent,
        "disk_total_gb": bytes_to_gb(disk.total),
        "disk_used_gb": bytes_to_gb(disk.used),
        "disk_free_gb": bytes_to_gb(disk.free),
        "net_sent_mb": round(network.bytes_sent / 1024 ** 2, 2),
        "net_recv_mb": round(network.bytes_recv / 1024 ** 2, 2),
        "net_packets_sent": network.packets_sent,
        "net_packets_recv": network.packets_recv,
        "net_errors_in": network.errin,
        "net_errors_out": network.errout,
        "net_drops_in": network.dropin,
        "net_drops_out": network.dropout,
        "uptime_minutes": int(time.time() - psutil.boot_time()) // 60,
        "process_count": len(psutil.pids()),
        "logged_in_users": len(psutil.users()),
        "hostname": hostname,
        "os": platform.system(),
        "os_version": platform.version(),
        "architecture": platform.machine(),
        "processor": platform.processor()
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
        if key in enabled_sensors:
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