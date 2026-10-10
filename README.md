# mqtt-iot-template

A small, **flat** MicroPython IoT starter application for RP2040/RP2350 and ESP32 boards. `net.py` handles Wi-Fi or Wiznet Ethernet connection setup; `main.py` runs `asyncio`, MQTT, a blinking onboard LED, and a worker thread on RP and ESP32 boards (without guaranteeing a separate core on ESP32).

Copyright © 2026 Sean Rieb. Licensed under the [MIT License](LICENSE).

## Files

| File | Purpose |
| --- | --- |
| `boot.py` | Optional MCU frequency setup at boot |
| `main.py` | Application tasks, MQTT, DNS, LED, optional worker thread (RP and ESP32) |
| `net.py` | Existing Wi-Fi/Ethernet initialization and reconnect support |
| `blinky.py` | Simple onboard LED helper (including RGB when configured) |
| `config.example.py` | Sample per-device Wi-Fi/MQTT configuration (copy to `config.py`) |

## Dependency

This template uses [seanrieb/async-mqtt](https://github.com/seanrieb/async-mqtt), maintained in a **separate** GitHub repository. The dependency is **not vendored** here. Install it to your MicroPython device with `mpremote`:

```bash
mpremote mip install github:seanrieb/async-mqtt
```

For reproducible deployments, install a tested release/tag of `async-mqtt` once one is published. Installing from the default branch may change over time.

## Setup and deployment

1. Install a compatible MicroPython firmware for your board and install `mpremote` on your computer (`python3 -m pip install mpremote`).
2. Copy `config.example.py` to **`config.py`**, then edit the Wi-Fi and MQTT settings. On Ethernet devices Wi-Fi SSID/password values are unused.
3. With the board connected over USB, install `async-mqtt` as shown above.
4. From this repository directory, upload the app files:

```bash
mpremote fs cp boot.py main.py net.py blinky.py config.py :
mpremote reset
```

The `mpremote fs cp` syntax and connection options can vary with your installed version; run `mpremote --help` if needed. The example assumes a single attached MicroPython board.

## What the demo does

- Starts a network task using `net.init()` and keeps checking connectivity.
- Initializes the DNS resolver from the interface's assigned DNS server.
- Subscribes to a configurable MQTT topic and publishes a counter every 100 ms.
- Toggles the onboard LED on every publish iteration.
- Runs a garbage-collection task and, on RP2040/RP2350 and ESP32, starts a worker thread. RP boards can use the second core; ESP32 does not guarantee a separate core.

Update the MQTT topics and broker in `config.py`. To add work in the worker thread, implement `core1_worker_step()` in `main.py`. Keep Wi-Fi, socket use and asyncio in the main thread.

## Board notes

`net.py` supports Pico W / Pico 2 W Wi-Fi, ESP32 Wi-Fi, and Wiznet variants where the MicroPython firmware exposes `network.WIZNET6K`. Board-specific SPI/PIO pin assignments are retained from the original implementation and may need adjustment for your exact board/firmware. `blinky.py` auto-detects some boards, but its default LED pin/RGB settings may require explicit configuration.

`boot.py` sets **250 MHz** on RP boards and **240 MHz** on ESP32. This is intentionally retained from the original template; 250 MHz is an overclock for many RP boards and may affect stability. Change or remove it for your hardware before deployment.

The project is a starting template rather than a production-ready network framework. Test network recovery, your specific board firmware, DNS, and MQTT reconnect behavior on physical hardware.

## GitHub

Public repository: https://github.com/seanrieb/mqtt-iot-template

Dependency: https://github.com/seanrieb/async-mqtt
