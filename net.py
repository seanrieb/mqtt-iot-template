# Copyright (c) 2026 Sean Rieb
# SPDX-License-Identifier: MIT

"""Portable MicroPython network initialization.

Supported targets:
  * Raspberry Pi Pico W / Pico 2 W (Wi-Fi)
  * ESP32 (Wi-Fi)
  * W5500-EVB-PICO / W5500-EVB-PICO2 (Ethernet)
  * W6300-EVB-PICO / W6300-EVB-PICO2 (Ethernet)
"""

import uasyncio as asyncio
import network
from os import uname
import utime
from machine import reset

nic = None
config = {
  "dhcp": True,
  "ip": None,
  "netmask": None,
  "gateway": "0.0.0.0",
  "dns": "0.0.0.0",
  "ssid": None,
  "password": None,
  "reset": False,
  "timeout": 10,
  "reboot": False,
  "hostname": None,
  "country": "US",
}
debug = False
_wifi = False
_reduce_power = False

if hasattr(network, "WLAN"):
  nic = network.WLAN(network.STA_IF)
  _wifi = True
  if uname()[0] == "rp2":
    _reduce_power = True

elif hasattr(network, "WIZNET6K"):
  if uname()[4].startswith("W6300"):
    from machine import Pin, WIZNET_PIO_SPI
    nic = network.WIZNET6K(
      WIZNET_PIO_SPI(
        baudrate=31250000,
        sck=Pin(17), cs=Pin(16),
        io0=Pin(18), io1=Pin(19),
        io2=Pin(20), io3=Pin(21)
      ),
      Pin(16), Pin(22)
    )
  elif uname()[4].startswith("RP2350-POE-ETH"):
    from machine import Pin, SPI
    nic = network.WIZNET6K(
      SPI(
        0,
        baudrate=31250000,
        sck=Pin(18),
        mosi=Pin(19), miso=Pin(16),
      ),
      Pin(17), Pin(20)
    )
  else:
    nic = network.WIZNET6K()

async def init():
  if nic is None:
    raise ValueError("Network module not available")

  if config["hostname"] is not None:
    try:
      network.hostname(config["hostname"])
    except (AttributeError, OSError):
      print("network: hostname not supported")
  if config["country"]:
    try:
      network.country(config["country"])
    except (AttributeError, OSError):
      pass

  if config["reset"]:
    nic.active(False)

  if _wifi:
    timeout = utime.time()+config["timeout"]
    while True:
      if not nic.active():
        nic.active(True)
        if _reduce_power:
          nic.config(pm=nic.PM_NONE)

        if config["dhcp"] is False:
          if config["ip"] is None or config["netmask"] is None:
            raise ValueError("IP/netmask not set")
          nic.ifconfig((config["ip"], config["netmask"], config["gateway"], config["dns"]))

        if config["ssid"] is None or config["password"] is None:
          raise ValueError("SSID/password not set")
        print("net: connecting to WiFi...")
        nic.connect(config["ssid"], config["password"])

      elif not nic.isconnected():
        if utime.time() > timeout:
          nic.active(False)
          await asyncio.sleep(1)
          if config["reboot"]:
            reset()
          timeout = utime.time()+config["timeout"]
        else:
          await asyncio.sleep_ms(500)

      else:
        break

  else:
    nic.active(True)
    print("net: waiting for link...")

    while nic.isconnected() is False:
      await asyncio.sleep_ms(250)

    print("net: link active")

    if config["dhcp"]:
      nic.ifconfig("dhcp")
    else:
      if config["ip"] is None or config["netmask"] is None:
        raise ValueError("IP/netmask not set")
      nic.ifconfig((config["ip"], config["netmask"], config["gateway"], config["dns"]))
