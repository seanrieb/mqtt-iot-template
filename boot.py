"""
boot.py

Runs 1st on after power up or reset
Use to configure hardware before the MicroPython subsystem and USB stack fully initialize.
Examples:
  - reconfigure USB interface (switch board from USB serial device to HID)
  - mounting or partitioning custom external storage or custom filesystems
  - selecting deep sleep wake-up pins before the main script launches

NOTE: Avoid infinite loops or long blocking delays.
"""

from os import uname
from machine import freq as machine_freq

if uname()[0] == "rp2":
  machine_freq(250_000_000)

if uname()[0] == "esp32":
  machine_freq(240_000_000)

# Initialize application peripherals only after changing the clock.
# Prefer doing that in main.py.