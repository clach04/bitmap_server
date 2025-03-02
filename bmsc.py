"""MicroPython nano-gui bitmap server client
https://github.com/clach04/bitmap_server
"""
import time

from color_setup import ssd  # Create a nano-gui display instance
from gui.core.nanogui import refresh
from gui.core.colors import create_color, RED, BLUE, GREEN, WHITE, BLACK

import network
import ntptime
import requests  # TODO async http, aiohttp

from microwifimanager.manager import WifiManager

try:
    import posix_tz  # https://github.com/clach04/py-posix_tz
except ImportError:
    posix_tz = None


def printable_mac(in_bytes, seperator=':'):
    if seperator:
        return seperator.join(['%02x' % x for x in in_bytes])
    else:
        return in_bytes.hex()

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
ssd.text('Connected to WiFi network: %s' % wlan.config('ssid'), 0, 18+8, WHITE)
refresh(ssd)
print("%r" % (wlan.ifconfig(),))  # IP address, subnet mask, gateway, DNS server
print("%r" % (wlan.config('mac'),))  # MAC in bytes
print("SSID: %r" % (wlan.config('ssid'),))
print("hostname: %r" % (network.hostname(),))
mac_addr_str = printable_mac(wlan.config('mac'))
print('Regular WiFi MAC      %r' % (mac_addr_str,))

print('pause for wifi to really be up')
print('URL %s' % url)
time.sleep(1)  # 1 second
ntptime.settime()  # TODO config for which server(s) to use for time lookup.

if posix_tz:
    posix_tz.set_tz('PST8PDT,M3.2.0/2:00:00,M11.1.0/2:00:00')  # TODO config
    print(posix_tz.localtime())

headers = {
    "ID": mac_addr_str,
    # TODO
    #"Access-Token": api_key),
    #"Refresh-Rate": str(refresh_rate)),  # seconds
    #"Battery-Voltage": str(battery_voltage)),  # max 5.0
    #"FW-Version": fw_version),  # '2.1.3'
    "RSSI": str(wlan.status('rssi')),
    "Width": str(ssd.width),
    "Height": str(ssd.height),
    # TODO does ssd contain a hint about bit-depth (and/or number of colors - for some eink displays number of colors may not completely match 2^bit-depth)?
    "_bpp": str(len(ssd.mvb) // (ssd.width * ssd.height // 8)),  # Bits Per Plane, i.e. color/bit-depth
}

r = requests.get(url, headers=headers)
# Not enough memory to use nice wrappers like content:
#   MemoryError: memory allocation failed, allocating 35992 bytes
r.raw.readinto(ssd.mvb)  # Read the image into the frame buffer)
refresh(ssd)
r.close()

# TODO every minute pull new image
# TODO regularly sync time
