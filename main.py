"""
main.py

Runs 2nd after boot.py finishes and MicroPython is initialized.
"""
import gc

import uasyncio as asyncio
import _thread
import gc
import sys
import utime
from machine import Pin
import net
from async_mqtt import MQTTClient
from async_mqtt.async_dns import Resolver
from blinky import Blinky

_dns: Resolver = None

###############################################################################
# Shared between core 0 and core 1
###############################################################################

# Shared, preallocated state:
#   [0] stop requested
#   [1] worker finished
#   [2] worker failed
_worker_state = bytearray(3)

_STOP = const(0)
_DONE = const(1)
_FAILED = const(2)

# Safely signals the asyncio loop from core 1.
_worker_changed = asyncio.ThreadSafeFlag()

###############################################################################
# CORE 1
###############################################################################

# Core 1 things to avoid:
#  Unprotected Shared Data
#    - Simultaneous variable access: Do not read or write global/shared variables across
#      Core 0 and Core 1 without using _thread.allocate_lock().
#    - Un-synchronized printing: Do not call print() on both cores at the exact same time;
#      wrap print statements in a lock or keep output restricted to one core to prevent
#      garbled text or data corruption
#  Hardware and Wi-Fi Operations
#    - Wireless/CYW43 actions: Do not run Wi-Fi commands, connect to networks, or call socket
#      methods (like socket.accept()) on Core 1. The wireless driver stack on Pico W / Pico 2 W
#      is not thread-safe and will crash or kill the
#    - Pin Interrupts (IRQ): Avoid setting up hardware pin interrupts (Pin(..., handler=...))
#      directly on Core 1, as interrupt handling behavior can fail or lock up depending on the
#      firmware build.
#  Memory and Output Conflicts
#    - Uncontrolled allocations: Try to limit heavy dynamic memory allocation or creation of
#      large local structures inside fast loops on Core 1 to prevent random heap fragmentation.
#    - Simultaneous UART/Stream writing: Avoid writing to the same UART or sys.stdout stream
#      from both cores concurrently, which causes character-duplication bugs and lockups


def core1_worker_step():
  pass


def core1_worker():
  try:
    while not _worker_state[_STOP]:
      core1_worker_step()
      # give some time back to python, can be removed under special circumstances
      utime.sleep(0)
  except BaseException as e:
    _worker_state[_FAILED] = 1
    try:
      print("Unhandled exception on core 1:")
      sys.print_exception(e)
    except:
      print("Unable to print core-1 exception")
  finally:
    _worker_state[_DONE] = 1
    try:
      _worker_changed.set()
    except:
      pass


###############################################################################
# CORE 0
###############################################################################


async def monitor_core1():
  while not _worker_state[_DONE]:
    await _worker_changed.wait()

  if _worker_state[_FAILED]:
    raise RuntimeError("Core 1 terminated with an exception")


async def shutdown_core1(timeout_ms=2000):
  _worker_state[_STOP] = 1
  deadline = utime.ticks_add(utime.ticks_ms(), timeout_ms)
  while not _worker_state[_DONE]:
    if utime.ticks_diff(deadline, utime.ticks_ms()) <= 0:
      print("Warning: core 1 did not stop before timeout")
      return False
    await asyncio.sleep_ms(10)
  return True


async def net_task():
  global _dns

  net.config["hostname"] = "astest"
  net.config["country"] = "US"
  net.config["ssid"] = "OpenWrt"
  net.config["password"] = ""
  net.config["reset"] = False

  while True:
    await net.init()

    addr, netmask, gateway, nameserver = net.nic.ifconfig()
    print(f"network: addr =       {addr}")
    print(f"network: netmask =    {netmask}")
    print(f"network: gateway =    {gateway}")
    print(f"network: nameserver = {nameserver}")
    _dns = Resolver(nameserver)

    while net.nic.isconnected():
      await asyncio.sleep_ms(200)

    print("network: lost connection")
    _dns = None


async def garbage_collector_task():
  while True:
    # Run collection at a predictable, relatively quiet interval.
    await asyncio.sleep_ms(5000)
    gc.collect()


async def on_message(client, topic, payload, retain, qos):
    print("mqtt:", topic, payload)


async def on_connect(client):
    print("mqtt: connected")


async def on_disconnect(client, error):
  print("mqtt: disconnected", error)


async def resolve(host, qtype="A"):
  if _dns is None:
    return None
  else:
    return await _dns.resolve(host, qtype)


async def main():
  asyncio.create_task(garbage_collector_task())

  led = Blinky()
  net.nic.active(False)

  client = MQTTClient(
    host="foobar.lan",
    port=1884,
    client_id="astest",
    on_message=on_message,
    on_connect=on_connect,
    on_disconnect=on_disconnect,
    reconnect_ms_min=200,
    reconnect_ms_max=1000,
    resolve=resolve,
  )
  await client.subscribe("commands/test/targetState")
  asyncio.create_task(client.run_forever())
  asyncio.create_task(net_task())

  count = 0
  while True:
    await client.publish(b"states/test/currentState", b"%d" % count)
    count += 1
    await asyncio.sleep_ms(100)
    led.toggle()


def wait_for_core1_blocking(timeout_ms=2000):
  """
  Fallback shutdown after the asyncio loop has stopped.
  """
  _worker_state[_STOP] = 1
  deadline = utime.ticks_add(utime.ticks_ms(), timeout_ms)

  while not _worker_state[_DONE]:
    if utime.ticks_diff(deadline, utime.ticks_ms()) <= 0:
      print("Warning: core 1 is still running")
      return False

    utime.sleep_ms(10)

  return True


def run():
  gc.enable()
  gc.collect()

  # now start thread
  _thread.start_new_thread(core1_worker, ())

  try:
    asyncio.run(main())

  except KeyboardInterrupt:
    print("\nKeyboard interrupt; shutting down")

  except BaseException as exc:
    print("Fatal exception on core 0:")
    sys.print_exception(exc)

  finally:
    wait_for_core1_blocking()

    # Discard references retained by the previous event loop.
    asyncio.new_event_loop()
    gc.collect()


if __name__ == "__main__":
  run()
