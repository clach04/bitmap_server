import os
import sys

import anywsgi
from anywsgi import not_found
from anywsgi import DEFAULT_LISTEN_ADDRESS, DEFAULT_SERVER_PORT


def application(environ, start_response):
    path_info = environ['PATH_INFO']
    print('%r' % (path_info,))
    if path_info != '/':
        return not_found(environ, start_response)
    start_response('200 OK',[('Content-type','text/html')])
    return [b'<html><body>Hello World!</body></html>']
    


print('Python %s on %s' % (sys.version, sys.platform))
listen_address = os.environ.get('LISTEN_ADDRESS', DEFAULT_LISTEN_ADDRESS)
server_port = int(os.environ.get('LISTEN_PORT', DEFAULT_SERVER_PORT))

"""FIXME seems to work fine...
But if open http://localhost:8080/ in Chrome
then "curl http://localhost:8080/", curl appears to hangs (actually takes a long time to respond, a little over 60 secs).
with built-in wsgiref.simple_server 0.2, which in Pyton 3 is http.server.HTTPServer, which is based on socketserver.TCPServer
"""
anywsgi.my_start_server(application, listen_address=listen_address, listen_port=server_port)
