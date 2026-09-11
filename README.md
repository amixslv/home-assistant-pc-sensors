# 🖥️ Home Assistant PC or Laptop Monitor

This Python script monitors PC or laptop sensors (battery, CPU, RAM, disk, network, uptime, etc.) and publishes them to Home Assistant via MQTT Discovery. Each device is automatically registered using its hostname, manufacturer, and model — no YAML configuration required.

---

## 📚 Table of Contents

- [✨ Features](#-features)
- [🧰 Requirements](#-requirements)
- [🔌 Home Assistant Setup](#-home-assistant-setup)
- [⚙️ Installation](#️-installation)
- [🚀 Auto-start on Windows](#-auto-start-on-windows)
- [📷 Screenshots](#-screenshots)
- [📄 License](#-license)

---

## ✨ Features

- ✅ MQTT Discovery support (no YAML needed)
- ✅ Dynamic device registration (hostname, manufacturer, model)
- ✅ Real-time charging status updates
- ✅ Works on any Windows PC or laptop
- ✅ Lightweight and efficient

---

## 🧰 Requirements

- [Python 3.x](https://www.python.org/downloads/)
- [Home Assistant](https://www.home-assistant.io/)
- MQTT broker (e.g. [Mosquitto](https://addons.home-assistant.io/addons/mosquitto/))
- MQTT integration enabled in Home Assistant

---

## 🔌 Home Assistant Setup

1. ✅ Install the **MQTT integration** in Home Assistant  
   👉 [Go to MQTT Integration](https://my.home-assistant.io/redirect/integration/?domain=mqtt)
    <p>
      <a href="https://my.home-assistant.io/redirect/integration/?domain=mqtt">
        <img src="https://img.shields.io/badge/Home%20Assistant-MQTT%20Integration-blue?logo=home-assistant&style=for-the-badge" alt="MQTT Integration">
      </a>
    </p>
    
3. ✅ Install the **Mosquitto broker** (if not already installed)  
   👉 [Go to Mosquitto Add-on](https://my.home-assistant.io/redirect/supervisor_addon/?addon=core_mosquitto)
    <p>
      <a href="https://my.home-assistant.io/redirect/supervisor_addon/?addon=core_mosquitto">
        <img src="https://img.shields.io/badge/Mosquitto-Broker-green?logo=eclipse-mosquitto&style=for-the-badge" alt="Mosquitto Broker">
      </a> 
    </p>

5. ✅ Create an MQTT user in Home Assistant  
   - Go to Mosquitto broker configuration
   - Create a user (e.g. `mqtt`) with a password
   - ![MQTT - 1752228635211](https://github.com/user-attachments/assets/b1f8f754-76e3-453f-aa1c-d12916ae817a)

6. ✅ Note your MQTT broker IP address (usually your HA IP)

---

## ⚙️ Installation

### 1. Clone or download this repository

```bash
git clone https://github.com/amixslv/home-assistant-pc-monitor.git
cd home-assistant-pc-monitor
```
### 2. Install required Python packages

```bash
pip install psutil paho-mqtt wmi
```
### 3. Configure MQTT

Copy `config.example.json` to `config.json`:

```powershell
Copy-Item ".\config.example.json" ".\config.json"
```

Open `config.json` and enter your MQTT broker settings:

```json
{
  "mqtt_broker": "192.168.x.x",
  "mqtt_port": 1883,
  "mqtt_topic_prefix": "home/laptop",
  "mqtt_user": "mqtt",
  "mqtt_pass": "your_password"
}
```

The settings are saved permanently, so they do not need to be entered after
each restart. `config.json` is excluded by `.gitignore`; do not remove it
from `.gitignore` or publish it. If your broker allows anonymous access,
leave both `mqtt_user` and `mqtt_pass` empty.

### 4. Run the script

```powershell
python ".\MQTT-PC sensors.py"
```
After a few seconds, your PC will appear in Home Assistant under Settings → Devices & Services → MQTT → Devices.

---

## 🚀 Auto-start on Windows

### 1. Open Task Scheduler

### 2. Create a new task:

  - Trigger: At log on
   
   - Action: Start a program
   
      - Program: python
      
      - Arguments: `"C:\Path\To\MQTT-PC sensors.py"`

Run with highest privileges

---

# 📷 Screenshots
## <img width="495" alt="image" src="https://github.com/user-attachments/assets/5bfa08ca-07e7-47f2-8173-952a7ad4d3e8" />

---
2026 © amixslv
