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
### 3. Edit MQTT credentials in MQTT-PC sensors.py

```bash
MQTT_BROKER = "192.168.x.x"
MQTT_USER = "your_usernama" # Mosquitto broker configuration username
MQTT_PASS = "your_password" # Mosquitto broker configuration password
```
P.S.
There are comments in the script that need to be adjusted.

### 4. Run the script

```bash
python MQTT-PC sensors.py
```
After a few seconds, your PC will appear in Home Assistant under Settings → Devices & Services → MQTT → Devices.

---

## 🚀 Auto-start on Windows

### 1. Open Task Scheduler

### 2. Create a new task:

  - Trigger: At log on
   
   - Action: Start a program
   
      - Program: python
      
      - Arguments: "C:\Path\To\MQTT-PC sensors.py"

Run with highest privileges

---

# 📷 Screenshots
## <img width="495" alt="image" src="https://github.com/user-attachments/assets/5bfa08ca-07e7-47f2-8173-952a7ad4d3e8" />

---
2025 © amixslv


