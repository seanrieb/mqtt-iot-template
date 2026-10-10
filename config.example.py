# Copyright (c) 2026 Sean Rieb
# SPDX-License-Identifier: MIT

# Copy this file to config.py and customize it for your board/network.
# config.py is intentionally excluded from Git.
NETWORK = {
    "hostname": "iot-device",
    "country": "US",
    "ssid": "YOUR_WIFI_SSID",       # Ignored on Ethernet boards
    "password": "YOUR_WIFI_PASSWORD",
    "dhcp": True,
    "reset": False,
    "timeout": 10,
    "reboot": False,
}

MQTT = {
    "host": "192.168.1.10",      # Replace with your broker address/name
    "port": 1883,
    "client_id": "iot-device",
    "username": None,
    "password": None,
    "publish_topic": "states/test/currentState",
    "subscribe_topic": "commands/test/targetState",
    "reconnect_ms_min": 1000,
    "reconnect_ms_max": 60000,
}
