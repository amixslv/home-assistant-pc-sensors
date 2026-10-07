# 🖥️ Home Assistant PC or Laptop Monitor

This Python script monitors PC or laptop sensors (battery, CPU, RAM, disk, network, uptime, etc.) and publishes them to Home Assistant using **MQTT Discovery**.  
It also supports **PC control** (restart, sleep, lock, brightness, power mode, etc.) — all fully configurable.

The script is **100% universal**:

- No YAML needed  
- No Python edits needed  
- All sensors, controls, and binary sensors are defined in `config.json`  
- Add/remove sensors or controls without touching the script  
- Works on any Windows PC or laptop  

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
