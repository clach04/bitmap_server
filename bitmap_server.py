#!/usr/bin/env python
# -*- coding: us-ascii -*-
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
#

import os
import sys

import anywsgi
from anywsgi import not_found
from anywsgi import DEFAULT_LISTEN_ADDRESS, DEFAULT_SERVER_PORT

# TODO version, and include in header response

# this file should be generated using a tool like:
#  * https://github.com/clach04/cyd_clocks/blob/main/image_converter.py
#  * https://github.com/peterhinch/micropython-nano-gui/blob/master/img_cvt.py
file_name = os.environ.get('BMS_BIN_FILE', 'bitmap_server.py')  # FIXME debug test for now
def application(environ, start_response):
    path_info = environ['PATH_INFO']
    print('%r' % (path_info,))
    if path_info != '/':
        return not_found(environ, start_response)

    # TODO handle errors and return something suitable to client
    f = open(file_name, 'rb')
    data = f.read()
    f.close()

    start_response('200 OK',[
        ('Content-type', 'application/octet-stream'),  # TODO consider application/x-binary, application/x-bms, application/x-bitmap-server, etc.
        ('Content-Length', str(len(data)))
    ])
    return [data]
    


print('Python %s on %s' % (sys.version, sys.platform))
listen_address = os.environ.get('LISTEN_ADDRESS', '0.0.0.0')
server_port = int(os.environ.get('LISTEN_PORT', DEFAULT_SERVER_PORT))

"""FIXME seems to work fine...
But if open http://localhost:8080/ in Chrome
then "curl http://localhost:8080/", curl appears to hangs (actually takes a long time to respond, a little over 60 secs).

Happens with:

  * built-in wsgiref.simple_server 0.2, which in Pyton 3 is http.server.HTTPServer, which is based on socketserver.TCPServer
  * werkzeug 3.1.3
"""
anywsgi.my_start_server(application, listen_address=listen_address, listen_port=server_port)
