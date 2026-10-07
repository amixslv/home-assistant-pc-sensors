import psutil
import paho.mqtt.client as mqtt
import time
import socket
import platform
import json
from pathlib import Path
import wmi
import subprocess

CONFIG_PATH = Path(__file__).with_name("config.json")

def load_configuration():
    try:
        with CONFIG_PATH.open(encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        raise RuntimeError("config.json not found")
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Invalid JSON in config.json: {e}")

config = load_configuration()

MQTT_BROKER = config["mqtt_broker"]
MQTT_PORT = config["mqtt_port"]
MQTT_TOPIC_PREFIX = config["mqtt_topic_prefix"]
MQTT_USER = config["mqtt_user"]
MQTT_PASS = config["mqtt_pass"]

UPDATE_INTERVAL = config["UPDATE_INTERVAL"]
CHECK_INTERVAL = config["CHECK_INTERVAL"]

sensors_cfg = config.get("sensors", [])
controls_cfg = config.get("controls", [])
binary_sensors_cfg = config.get("binary_sensors", [])

hostname = socket.gethostname()
discovery_prefix = "homeassistant"
prev_values = {}

def create_mqtt_client():
    client = mqtt.Client()
    if MQTT_USER:
        client.username_pw_set(MQTT_USER, MQTT_PASS)
    return client

def get_system_info():
    try:
        c = wmi.WMI()
        system = c.Win32_ComputerSystem()[0]
        return system.Manufacturer, system.Model
    except Exception:
        return "Unknown", "Unknown"

manufacturer, model = get_system_info()

def validate_configuration():
    if not MQTT_BROKER or MQTT_BROKER == "192.168.x.x":
        raise ValueError("Set mqtt_broker in config.json")
    if MQTT_USER and not MQTT_PASS:
        raise ValueError("Set mqtt_pass in config.json or clear mqtt_user")

def publish_discovery_sensors(client):
    device = {
        "identifiers": [hostname],
        "name": hostname,
        "manufacturer": manufacturer,
        "model": model
    }

    for s in sensors_cfg:
        key = s["key"]
        name = s.get("name", key)
        config_topic = f"{discovery_prefix}/sensor/{hostname}_{key}/config"
        state_topic = f"{MQTT_TOPIC_PREFIX}/{hostname}/{key}"

        payload = {
            "name": name,
            "state_topic": state_topic,
            "unique_id": f"{hostname}_{key}",
            "device": device
        }

        if s.get("unit"):
            payload["unit_of_measurement"] = s["unit"]
        if s.get("device_class"):
            payload["device_class"] = s["device_class"]
        if s.get("icon"):
            payload["icon"] = s["icon"]

        client.publish(config_topic, json.dumps(payload), retain=True)

def publish_discovery_controls(client):
    device = {
        "identifiers": [hostname],
        "name": hostname,
        "manufacturer": manufacturer,
        "model": model
    }

    for ctrl in controls_cfg:
        entity_type = ctrl["type"]
        unique_id = ctrl["unique_id"]
        name = ctrl["name"]
        command = ctrl["command"]

        config_topic = f"{discovery_prefix}/{entity_type}/{hostname}_{unique_id}/config"
        command_topic = f"{MQTT_TOPIC_PREFIX}/{hostname}/commands/{command}"
        state_topic = f"{MQTT_TOPIC_PREFIX}/{hostname}/state/{command}"

        payload = {
            "name": name,
            "unique_id": f"{hostname}_{unique_id}",
            "device": device,
            "command_topic": command_topic
        }

        if entity_type in ("switch", "select", "number"):
            payload["state_topic"] = state_topic

        if entity_type == "switch":
            payload["payload_on"] = ctrl["payload_on"]
            payload["payload_off"] = ctrl["payload_off"]

        if entity_type == "select":
            payload["options"] = ctrl["options"]

        if entity_type == "number":
            payload["min"] = ctrl["min"]
            payload["max"] = ctrl["max"]
            payload["step"] = ctrl["step"]
            payload["mode"] = "auto"
            payload["unit_of_measurement"] = ctrl["unit"]

        client.publish(config_topic, json.dumps(payload), retain=True)

    for bs in binary_sensors_cfg:
        config_topic = f"{discovery_prefix}/binary_sensor/{hostname}_{bs['unique_id']}/config"
        state_topic = f"{MQTT_TOPIC_PREFIX}/{hostname}/{bs['state']}"

        payload = {
            "name": bs["name"],
            "unique_id": f"{hostname}_{bs['unique_id']}",
            "state_topic": state_topic,
            "device": device
        }

        client.publish(config_topic, json.dumps(payload), retain=True)

def eval_sensor(expr):
    try:
        return eval(expr, {
            "psutil": psutil,
            "platform": platform,
            "Path": Path,
            "time": time,
            "hostname": hostname
        })
    except Exception as e:
        print(f"[ERROR] Sensor expr failed: {expr} -> {e}")
        return None

def get_sensors():
    result = {}
    for s in sensors_cfg:
        key = s["key"]
        expr = s["expr"]
        result[key] = eval_sensor(expr)
    return result

def execute_control(ctrl, payload):
    t = ctrl["type"]
    cmd = None

    if t == "switch":
        if payload == ctrl["payload_on"]:
            cmd = ctrl.get("exec_on")
        elif payload == ctrl["payload_off"]:
            cmd = ctrl.get("exec_off")

    elif t == "button":
        cmd = ctrl.get("exec")

    elif t == "select":
        cmd = ctrl.get("exec_map", {}).get(payload)

    elif t == "number":
        template = ctrl.get("exec", "")
        cmd = template.replace("{value}", str(payload))

    if cmd:
        try:
            subprocess.run(cmd, shell=True)
        except Exception as e:
            print(f"[ERROR] Command failed: {cmd} -> {e}")

def publish_control_state(client, command, value):
    topic = f"{MQTT_TOPIC_PREFIX}/{hostname}/state/{command}"
    client.publish(topic, value, retain=True)

def publish_binary_state(client, key, value):
    topic = f"{MQTT_TOPIC_PREFIX}/{hostname}/{key}"
    client.publish(topic, json.dumps(bool(value)), retain=True)

def on_message(client, userdata, msg):
    payload = msg.payload.decode(errors="ignore")
    command = msg.topic.split("/")[-1]

    for ctrl in controls_cfg:
        if ctrl["command"] == command:
            execute_control(ctrl, payload)
            publish_control_state(client, command, payload)

            if command == "lock":
                publish_binary_state(client, "locked", True)
                publish_binary_state(client, "active", False)

            if command == "sleep":
                publish_binary_state(client, "sleeping", True)
                publish_binary_state(client, "active", False)

            if command == "power" and payload == ctrl.get("payload_on"):
                publish_binary_state(client, "active", True)

            return

def publish_if_changed(client, key, value):
    if prev_values.get(key) != value:
        topic = f"{MQTT_TOPIC_PREFIX}/{hostname}/{key}"
        if isinstance(value, bool):
            payload = json.dumps(value)
        else:
            payload = value
        client.publish(topic, payload, retain=True)
        prev_values[key] = value
        print(f"[CHANGED] {key} -> {value}")

def publish_sensors(client, sensors):
    for key, value in sensors.items():
        publish_if_changed(client, key, value)

def main():
    validate_configuration()
    client = create_mqtt_client()
    client.on_message = on_message
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.subscribe(f"{MQTT_TOPIC_PREFIX}/{hostname}/commands/#")
    client.loop_start()

    publish_discovery_sensors(client)
    publish_discovery_controls(client)

    publish_binary_state(client, "locked", False)
    publish_binary_state(client, "sleeping", False)
    publish_binary_state(client, "active", True)

    publish_sensors(client, get_sensors())
    next_full_update = time.monotonic() + UPDATE_INTERVAL

    try:
        while True:
            time.sleep(CHECK_INTERVAL)
            now = time.monotonic()
            if now >= next_full_update:
                publish_sensors(client, get_sensors())
                next_full_update = now + UPDATE_INTERVAL
            else:
                # battery-only quick update
                battery_only = {
                    s["key"]: eval_sensor(s["expr"])
                    for s in sensors_cfg
                    if "battery" in s["key"]
                }
                publish_sensors(client, battery_only)

    except KeyboardInterrupt:
        print("Stopping...")

    finally:
        client.loop_stop()
        client.disconnect()

if __name__ == "__main__":
    main()
