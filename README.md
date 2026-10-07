# 🖥️ Home Assistant PC or Laptop Monitor

This Python script monitors PC or laptop sensors (battery, CPU, RAM, disk, network, uptime, etc.) and publishes them to Home Assistant using **MQTT Discovery**.  
It also supports **PC control** (restart, sleep, lock, brightness, power mode, etc.) — all fully configurable.

---

## ✨ Features

- 🚀 **Fully universal architecture** — everything is defined in `config.json`
- 🧠 **Dynamic sensors via Python expressions (`expr`)**
- 🔌 **MQTT Discovery** (automatic device creation in Home Assistant)
- 🖥️ **PC control** (restart, sleep, lock, brightness, power mode, etc.)
- 🔋 Real-time battery and charging status
- 💡 Works on any Windows PC or laptop
- ⚡ Lightweight and efficient

---

## 🧰 Requirements

- Python 3.8+
- Home Assistant
- MQTT broker (Mosquitto recommended)
- MQTT integration enabled
- Python packages:
  ```bash
  pip install psutil paho-mqtt wmi
