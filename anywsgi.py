#!/usr/bin/env python
# -*- coding: us-ascii -*-
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
#
# anywsgi.py - Use any available WSGI server
# Copyright (C) 2024  Chris Clark
"""Quick and dirty WSGI runner

TODO Jython - modjy
TODO Jython - https://github.com/jythontools/fireside
TODO Gunicorn 'Green Unicorn
"""

try:
    # Python 3.8 and later
    # py3
    from html import escape as escape_html
except ImportError:
    # py2
    from cgi import escape as escape_html

import logging
import os
import platform
import sys
import wsgiref
from wsgiref.simple_server import make_server

try:
    import bjoern  # https://pypi.org/project/bjoern/
    """NOTE appears to be missing a bunch of stuff, from environ:

        environ.get('CONTENT_TYPE'))
        environ.get('QUERY_STRING'))

    (Automatic) Response headers missing Date, bjoern does NOT include this by default, where as wsgiref does
    """
except ImportError:
    bjoern = None

try:
    import cheroot  # CherryPy Server https://cheroot.cherrypy.dev/en/latest/pkg/cheroot.wsgi/
    import cheroot.wsgi
except ImportError:
    cheroot = None

try:
    import cherrypy
except ImportError:
    cherrypy = None

try:
    import meinheld  # https://github.com/mopemope/meinheld
except ImportError:
    meinheld = None

try:
    import waitress   # https://github.com/Pylons/waitress
except ImportError:
    waitress  = None

try:
    import werkzeug  # https://github.com/pallets/werkzeug/
    import werkzeug.serving
except ImportError:
    werkzeug = None


log = logging.getLogger(__name__)
logging.basicConfig()
log.setLevel(level=logging.INFO)
log.setLevel(level=logging.DEBUG)


DEFAULT_SERVER_PORT = 8080
DEFAULT_LISTEN_ADDRESS = '127.0.0.1'

def force_bool(in_bool):
    """Force string value into a Python boolean value
    Everything is True with the exception of; false, off, and 0"""
    value = str(in_bool).lower()
    if value in ('false', 'off', '0'):
        return False
    else:
        return True

def to_bytes(in_str):
    # could choose to only encode for Python 3+
    return in_str.encode('utf-8')

def not_found(environ, start_response):
    """serves 404s."""
    #start_response('404 NOT FOUND', [('Content-Type', 'text/plain')])
    #return ['Not Found']
    start_response('404 NOT FOUND', [('Content-Type', 'text/html')])
    return [to_bytes('''<!DOCTYPE HTML PUBLIC "-//IETF//DTD HTML 2.0//EN">
<html><head>
<title>404 Not Found</title>
</head><body>
<h1>Not Found</h1>
<p>The requested URL /??????? was not found on this server.</p>
</body></html>''')]


def cutoff(s, n=100):
    if len(s) > n: return s[:n]+ '.. cut ..'
    return s


# A relatively simple WSGI application. It's going to print out the
# environment dictionary after being updated by setup_testing_defaults
def simple_app(environ, start_response):
    status = '200 OK'
    headers = [('Content-type', 'text/html; charset=utf-8')]

    start_response(status, headers)

    ret = []
    ret += [('Python %s on %s\n\n' % (sys.version, sys.platform)).encode('utf-8')]
    ret += ['web environ\n'.encode('utf-8')]
    ret += ["<table border='1'>".encode('utf-8')]
    ret += [("<tr><td>%s</td><td>%s</td></tr>\n" % (key, escape_html(cutoff(str(value))))).encode("utf-8")
           for key, value in environ.items()]
    ret += ["</table>".encode('utf-8')]

    ret += ['\n'.encode('utf-8')]
    ret += ['\n'.encode('utf-8')]
    ret += ['os environ\n'.encode('utf-8')]
    ret += ["<table border='1'>".encode('utf-8')]
    ret += [("<tr><td>%s</td><td>%s</td></tr>\n" % (key, escape_html(cutoff(str(value))))).encode("utf-8")
           for key, value in os.environ.items()]
    ret += ["</table>".encode('utf-8')]
    return ret


def my_start_server(callable_app, listen_address=DEFAULT_LISTEN_ADDRESS, listen_port=DEFAULT_SERVER_PORT):
    if listen_address == '':
        listen_address = '0.0.0.0'
    if listen_address == '0.0.0.0':
        local_ip = '127.0.0.1'
    else:
        local_ip = listen_address
    log.info('open : http://%s:%d', 'localhost', listen_port)
    log.info('open : http://%s:%d', local_ip, listen_port)
    log.info('open : http://%s:%d', platform.node(), listen_port)

    # Try servers in the order I personally prefer ;-)
    if werkzeug:
        import importlib.metadata
        #log.info('Using: werkzeug %s', werkzeug.__version__)
        log.info('Using: werkzeug %s', importlib.metadata.version("werkzeug"))
        #werkzeug.serving.run_simple(listen_address, listen_port, callable_app, use_debugger=True, use_reloader=True)
        werkzeug.serving.run_simple(listen_address, listen_port, callable_app, use_debugger=False, use_reloader=False)
    elif waitress:
        log.info('Using: waitress%s', waitress.__version__)
        waitress.serve(callable_app, host=listen_address, port=listen_port)
    elif cheroot:
        log.info('Using: cheroot %s', cheroot.__version__)
        server = cheroot.wsgi.Server((listen_address, listen_port), callable_app)  # '' untested for address
        server.start()
    elif cherrypy:
        log.info('Using: cherrypy %s', cherrypy.__version__)
        # tested with cherrypy-18.8.0 and cheroot-9.0.0
        # Mount the application
        cherrypy.tree.graft(callable_app, "/")

        # Unsubscribe the default server
        cherrypy.server.unsubscribe()

        # Instantiate a new server object
        server = cherrypy._cpserver.Server()

        # Configure the server object
        server.socket_host = listen_address
        server.socket_port = listen_port
        #server.thread_pool = 30

        # For SSL Support
        # server.ssl_module            = 'pyopenssl'
        # server.ssl_certificate       = 'ssl/certificate.crt'
        # server.ssl_private_key       = 'ssl/private.key'
        # server.ssl_certificate_chain = 'ssl/bundle.crt'

        # Subscribe this server
        server.subscribe()

        # Start the server engine (Option 1 *and* 2)
        cherrypy.engine.start()
        cherrypy.engine.block()
    elif bjoern:
        log.info('Using: bjoern %r', bjoern._bjoern.version)
        if listen_address == '0.0.0.0':
            listen_address = ''
        bjoern.run(callable_app, listen_address, listen_port)  # TODO REVIEW should this be; callable_app()
    elif meinheld:
        # Untested, Segmentation fault when serving a file :-(
        meinheld.server.listen(('0.0.0.0', listen_port))  # does not accept ''
        meinheld.server.run(simple_app)
    else:
        log.info('Using: wsgiref.simple_server %s', wsgiref.simple_server.__version__)
        # TODO should listen_address = '' when listen_address was set to 0.0.0.0?
        httpd = wsgiref.simple_server.make_server(listen_address, listen_port, callable_app)
        httpd.serve_forever()


def main(argv=None):
    print('Python %s on %s' % (sys.version, sys.platform))
    listen_address = os.environ.get('LISTEN_ADDRESS', DEFAULT_LISTEN_ADDRESS)
    server_port = int(os.environ.get('PORT', DEFAULT_SERVER_PORT))
    always_return_404 = force_bool(os.environ.get('ALWAYS_RETURN_404', False))

    print("always_return_404 = %r" % always_return_404)
    log.info('Starting server: %r', (listen_address, server_port))
    log.info('Open: http://%s:%d', listen_address, server_port)
    if always_return_404:
        wsgi_demo_app = not_found
    else:
        wsgi_demo_app = simple_app
    my_start_server(wsgi_demo_app, listen_address=listen_address, listen_port=server_port)

if __name__ == "__main__":
    sys.exit(main())
