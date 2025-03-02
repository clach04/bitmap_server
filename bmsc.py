"""MicroPython nano-gui bitmap server client
https://github.com/clach04/bitmap_server
"""
import time

from color_setup import ssd  # Create a nano-gui display instance
from gui.core.nanogui import refresh
from gui.core.colors import create_color, RED, BLUE, GREEN, WHITE, BLACK

import asyncio
import json
import network
import ntptime
import requests  # TODO async http, aiohttp

from microwifimanager.manager import WifiManager

from sched.sched import schedule, Sequence  # https://github.com/peterhinch/micropython-async/blob/master/v3/docs/SCHEDULE.md

try:
    import posix_tz  # https://github.com/clach04/py-posix_tz
except ImportError:
    posix_tz = None


def printable_mac(in_bytes, seperator=':'):
    if seperator:
        return seperator.join(['%02x' % x for x in in_bytes])
    else:
        return in_bytes.hex()

def get_config(fn='clock.json'):  # TODO consider using https://github.com/Uthayamurthy/ConfigManager-Micropython (note it uses regexes...)
    # NOTE less memory if just try and open file and deal with errors
    try:
        with open(fn) as f:
            c = json.load(f)
    except:
        # yeah, bare except, gulp :-(
        c = {}
    # dumb update/merge for defaults
    c['TZ'] = c.get('TZ', 'PST8PDT,M3.2.0/2:00:00,M11.1.0/2:00:00')
    c['url'] = c.get('url', 'http://192.168.11.101:1299')
    # TODO NTP Server list
    return c


refresh(ssd, True)  # Initialise and clear display.
config = get_config()

# Uncomment for ePaper displays
# ssd.wait_until_ready()

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
print('URL %s' % config['url'])
time.sleep(1)  # 1 second
ntptime.settime()  # TODO config for which server(s) to use for time lookup.

if posix_tz:
    posix_tz.set_tz(config['TZ'])
    print(posix_tz.localtime())

def get_and_update_display():
    # FIXME headers do not need to be re-created each time, create once and update for things that can change
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

    r = requests.get(config['url'], headers=headers)
    # Not enough memory to use nice wrappers like content:
    #   MemoryError: memory allocation failed, allocating 35992 bytes
    r.raw.readinto(ssd.mvb)  # Read the image into the frame buffer)
    refresh(ssd)
    r.close()

# TODO every minute pull new image

async def main():
    # TODO review all schedule options/APIs (like cron)
    # TODO look at sleep options, specifically for eink, look at deep sleep for display (as well as CPU) and use a hardware timer/wakeup
    seq = Sequence()
    asyncio.create_task(schedule(seq, 'every 1 min', hrs=None, mins=range(0, 60, 1)))
    # TODO regularly sync time
    async for args in seq:
        #print('scheduler args %r' % (args,))  # scheduler args ('every 1 min',)
        if posix_tz:
            print(posix_tz.localtime())
        get_and_update_display()

try:
    get_and_update_display()  # maybe call this elsewhere? First time call
    asyncio.run(main())
finally:
    _ = asyncio.new_event_loop()
