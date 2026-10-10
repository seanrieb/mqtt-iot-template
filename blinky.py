
"""Board-independent onboard LED control for MicroPython."""

import os
from machine import Pin


class Blinky:
    """
    Onboard LED controller.

    Supported boards:
      - Raspberry Pi Pico / Pico W / Pico 2 / Pico 2 W
      - ESP32 (LED pin may require configuration)
      - Waveshare RP2350-POE-ETH (WS2812 RGB)

    Parameters:
      board:  "auto", "pico", "esp32", or "rp2350-poe-eth"
      pin:    Optional GPIO number or "LED"
      rgb:    Override RGB mode (True/False)
      color:  Default RGB color (R, G, B)
      active_low: LED is active when GPIO is low
    """

    def __init__(
        self,
        board="auto",
        pin=None,
        rgb=None,
        color=(0, 32, 0),
        active_low=False,
    ):
        self._state = False
        self._color = tuple(color)
        self._active_low = active_low

        info = os.uname()
        machine_name = (
            getattr(info, "machine", "") + " " +
            getattr(info, "sysname", "")
        ).lower()

        if board == "auto":
            if "poe-eth" in machine_name:
                board = "rp2350-poe-eth"
            elif "esp32" in machine_name:
                board = "esp32"
            elif "rp2040" in machine_name or "rp2350" in machine_name:
                board = "pico"
            else:
                board = "generic"

        if rgb is None:
            rgb = board == "rp2350-poe-eth"

        self._rgb = rgb

        if pin is None:
            if board == "rp2350-poe-eth":
                pin = 25
            elif board == "esp32":
                # Common ESP32 DevKit onboard LED.
                # Other models may need an explicit pin.
                pin = 2
            else:
                pin = "LED"

        if self._rgb:
            import neopixel
            self._led = neopixel.NeoPixel(Pin(pin, Pin.OUT), 1)
        else:
            try:
                self._led = Pin(pin, Pin.OUT)
            except (ValueError, TypeError):
                if pin == "LED":
                    self._led = Pin(25, Pin.OUT)
                else:
                    raise

        self.off()

    def _write(self):
        if self._rgb:
            self._led[0] = (
                self._color if self._state else (0, 0, 0)
            )
            self._led.write()
        else:
            level = self._state != self._active_low
            self._led.value(int(level))

    def on(self, color=None):
        """Turn LED on, optionally changing RGB color."""
        if color is not None:
            self._color = tuple(color)

        self._state = True
        self._write()

    def off(self):
        """Turn LED off."""
        self._state = False
        self._write()

    def toggle(self):
        """Toggle LED state and return new state."""
        self._state = not self._state
        self._write()
        return self._state

    def value(self, state=None):
        """Get or set LED state (0 or 1)."""
        if state is None:
            return int(self._state)

        if state:
            self.on()
        else:
            self.off()

        return int(self._state)

    def color(self, color=None):
        """Get or set RGB color."""
        if color is None:
            return self._color

        self._color = tuple(color)

        if self._rgb and self._state:
            self._write()

    def is_on(self):
        """Return True if LED is on."""
        return self._state
