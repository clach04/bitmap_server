"""MicroPython nano-gui bitmap server client
https://github.com/clach04/bitmap_server
"""

from color_setup import ssd  # Create a nano-gui display instance
from gui.core.nanogui import refresh
from gui.core.colors import create_color, RED, BLUE, GREEN, WHITE, BLACK

import network
import requests  # TODO async http, aiohttp

from microwifimanager.manager import WifiManager


refresh(ssd, True)  # Initialise and clear display.

# Uncomment for ePaper displays
# ssd.wait_until_ready()

url = "http://192.168.11.101:1299"  # TODO config
ssid = 'bmsc'


network.hostname(ssid.lower())  # TODO + last 4 digits of mac?
ssd.text('Trying to start WiFi', 0, 10, WHITE)  # 8x8 built in font
ssd.text('ssid: %s' % ssid, 0, 18, WHITE)
refresh(ssd)
wlan = None
wfm = WifiManager(ssid=ssid)
while wlan is None:
    print("Trying to start WiFi network connection.")
    wlan = wfm.get_connection()
print("Connected to WiFi network")
print("%r" % (wlan.ifconfig(),))  # IP address, subnet mask, gateway, DNS server
print("%r" % (wlan.config('mac'),))  # MAC in bytes
print("SSID: %r" % (wlan.config('ssid'),))
print("hostname: %r" % (network.hostname(),))


r = requests.get(url)
# Not enough memory to use nice wrappers like content:
#   MemoryError: memory allocation failed, allocating 35992 bytes
r.raw.readinto(ssd.mvb)  # Read the image into the frame buffer)
refresh(ssd)
r.close()
