#!/usr/bin/env python
# -*- coding: us-ascii -*-
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
#

import datetime
from io import BytesIO as FakeFile
import os
import sys

try:
    from PIL import Image  # http://www.pythonware.com/products/pil/
    from PIL import ImageFont, ImageDraw, ImageOps
except ImportError:
    try:
        import Image  # http://www.pythonware.com/products/pil/
        import ImageFont
        import ImageDraw
        import ImageOps
    except ImportError:
        raise  # Potential to remove dependency on PIL

import anywsgi
from anywsgi import not_found
from anywsgi import DEFAULT_LISTEN_ADDRESS, DEFAULT_SERVER_PORT


is_py3 = sys.version_info >= (3,)

################################################

# https://github.com/peterhinch/micropython-nano-gui/blob/77f58af1fab27e0ec6ba959a2b04cd4061fa828f/gui/core/colors.py#L14..L27
nano_gui_palette = [
    0, 0, 0,        # BLACK
    0, 255, 0,      # GREEN
    255, 0, 0,      # RED
    140, 0, 0,      # LIGHTRED  (actually dark-red)
    0, 0, 255,      # BLUE
    255, 255, 0,    # YELLOW
    100, 100, 100,  # GREY
    255, 0, 255,    # MAGENTA
    0, 255, 255,    # CYAN
    0, 100, 0,      # LIGHTGREEN
    0, 80, 0,       # DARKGREEN
    0, 0, 90,       # DARKBLUE
    75, 75, 75,     # 12 light-Grey  # NOTE not a reserved nano-color
    150, 150, 150,  # 13 darker-Grey  # NOTE not a reserved nano-color
    200, 200, 200,  # 14 darkest-Grey  # NOTE not a reserved nano-color
    255, 255, 255,  # WHITE
]
NANO_COLOR_BLACK = 0
NANO_COLOR_GREEN = 1
NANO_COLOR_RED = 2
NANO_COLOR_LIGHTRED = DARKRED = 3  # mislabeled - https://github.com/peterhinch/micropython-nano-gui/issues/95
NANO_COLOR_BLUE = 4
NANO_COLOR_YELLOW = 5
NANO_COLOR_GREY = 6
NANO_COLOR_MAGENTA = 7
NANO_COLOR_CYAN = 8
NANO_COLOR_LIGHTGREEN = 9
NANO_COLOR_DARKGREEN = 10
NANO_COLOR_DARKBLUE = 11
NANO_COLOR_LIGHTGREY = 12  # NOTE not a reserved nano-color
NANO_COLOR_DARKERGREY = 13  # NOTE not a reserved nano-color
NANO_COLOR_DARKESTGREY = 14  # NOTE not a reserved nano-color
NANO_COLOR_WHITE = 15


def mygetpalette(pal_type, orig_image_palette):
    # return palette list of tuples in RGB order
    palette = []
    if pal_type != "RGB":
        return palette
    image_palette = orig_image_palette[:]
    while image_palette != []:
        r = image_palette.pop(0)
        g = image_palette.pop(0)
        b = image_palette.pop(0)
        palette.append( (r, g, b) )
    return palette

def convert_image(image):
    """TODOs
      * color reduction/conversion?
          * dither options?
      * rotation
      * mirror
      * flip?
      * maybe add resize support?
    """

    color_count = 16  # 4-bit color depth
    dither_none = Image.NONE  # Image.Dither.NONE
    im = image.convert("P", dither=dither_none, palette=Image.ADAPTIVE, colors=color_count)  # TODO preset pallete, dither options...
    width, height = im.size
    try:
        if im.info["transparency"] == 0:
            transparency = True
    except KeyError:
        transparency = False

    # FIXME more sanity checks
    # FIXME sanity check; no transparency
    # FIXME sanity check; bit depth 4 or less

    # Sanity checks on assumptions
    if 'getdata' not in dir(im.palette):
        raise NotImplementedError('image must be indexed, try a PNG or GIF')
    pal_type, pal_data = im.palette.getdata()
    if pal_type not in ("RGB", "RGB;L"):
        raise NotImplementedError('Need RGB palette, try a PNG file (instead of BMP)')

    print(pal_data)
    if is_py3:
        pal_data = list(pal_data)
    else:
        pal_data = list(map(ord, pal_data))  # py2 bytes to ints

    indexed_palette = mygetpalette(pal_type,pal_data) ## must contain accurate palette

    print(indexed_palette)
    for entry in indexed_palette:
        print(entry)

    pixels = list(im.getdata())
    """
    for x in im.getdata():
        print(x)
    print('')
    print(pixels)
    """

    # generate format than nano-gui recommends; 2 byte ints for dimensions, then pixel data 4-bits each for index (into palette)
    fo = FakeFile()  # TODO don't really need to use a file API
    fo.write(b"".join((height.to_bytes(2, "big"), width.to_bytes(2, "big"))))

    pixel_counter = 0
    nibbles = [0, 0]
    while pixel_counter < len(pixels):
        for n in range(2):
            c = pixels[pixel_counter]
            nibbles[n] = c
            pixel_counter += 1
        fo.write(int.to_bytes((nibbles[0] << 4) | nibbles[1], 1, "big"))

    return fo.getvalue()


def generate_image(format='png', screen_width=None, screen_height=None):
    """TODOs config option
      * 24/12 hour config option
      * 1-bit/4-bit/8-bit color config option
      * color selection for; backround, digit(s), and arc
      * screen dimensions config option
      * font name
      * font size override

    Ideas:
      * bitmap digits (rather than font)
    """
    screen_res = (int(screen_width or 320), int(screen_height or 240))  # TODO bother with error handling here for non-numeric params?
    SCREEN_WIDTH, SCREEN_HEIGHT = screen_res[0], screen_res[1]  # TODO min/max support?

    # figure out centered view
    # assume square pixels for easier math
    # TODO add margin support
    min_pixel_length = min(SCREEN_WIDTH, SCREEN_HEIGHT)
    print(min_pixel_length)
    if min_pixel_length == SCREEN_WIDTH:
        offset = (SCREEN_HEIGHT - min_pixel_length) // 2
        circle_box = (0, offset, 0 + min_pixel_length, offset + min_pixel_length)
    else:
        offset = (SCREEN_WIDTH - min_pixel_length) // 2
        circle_box = (offset, 0, offset + min_pixel_length, 0 + min_pixel_length)
    print(circle_box)


    # FIXME / TODO config
    background_color = NANO_COLOR_BLACK
    digit_color = NANO_COLOR_CYAN
    arc_color = NANO_COLOR_WHITE
    #arc_color = digit_color  # 'blue'
    arc_width = min_pixel_length // 10  # pixels
    font_size = 72
    font_size = arc_width * 5
    print(font_size)

    # FIXME / TODO do once
    clock_font = None
    #clock_font = ImageFont.load_default()  # too small
    # TODO config font lists
    for font_filename, font_size in [
                                        ('freesansbold.ttf', font_size),  # https://github.com/opensourcedesign/fonts/blob/master/gnu-freefont_freesans/FreeSansBold.ttf
                                        ('FreeSansBold.ttf', font_size),
                                        ('/usr/share/fonts/truetype/freefont/FreeSansBold.ttf', font_size),
                                        ('DejaVuSans-Bold.ttf', font_size),  # related to FreeSansBold
                                        ('Courier', font_size),
                                        # Windows builtin backup fonts, not great fonts but at least have a font
                                        ('courbd', font_size),
                                        ('cour', font_size),
                                    ]:
        try:
            # https://pillow.readthedocs.io/en/stable/reference/ImageFont.html#PIL.ImageFont.truetype
            # ImageFont.truetype(font, size); size, in pixels.
            clock_font = ImageFont.truetype(font_filename, font_size)
            #log.debug('font %r %r', font_filename, font_size)
            print('font %r %r' %(font_filename, font_size))
            break
        except IOError:
            pass

    if not clock_font:
        raise NotImplementedError('No font available')

    # https://pillow.readthedocs.io/en/stable/reference/ImageFont.html#PIL.ImageFont.FreeTypeFont.getbbox
    # pre-calculating this with 2 digits does NOT work for 1 digit :-(
    try:
        clock_font_box = clock_font.getbbox('00')  # with older PIL ('7.0.0') not available; AttributeError: 'FreeTypeFont' object has no attribute 'getbbox'. Fine with Pillow PIL.__version__ == 11.1.0
        clock_font_width, clock_font_height = clock_font_box[2], clock_font_box[3]
        print('clock_font_box %r' % (clock_font_box,))
    except :
        clock_font_width, clock_font_height = clock_font.getsize('00')

    print('clock_font sizes %r' % ((clock_font_width, clock_font_height),))

    mode = 'L'  # Mono, B/W, Black and White - 1-bit color depth
    mode = 'P'  # palette
    image = Image.new(mode, screen_res, background_color)
    image.putpalette(nano_gui_palette)  # setup palette/index
    draw = ImageDraw.Draw(image)

    now = datetime.datetime.now()

    hours = now.hour
    minutes = now.minute
    #hours, minutes = 1, 59
    #hours, minutes = 23, 59

    """
    hours = 11
    minutes = 15

    degree = 90  # for 15 mins, quarter of an hour
    degree = 180  # for 30 mins, half of an hour
    degree = 270  # for 45 mins, three-quarter of an hour
    """

    # default to hours as digits, hours as an arc/circle
    degree = minutes * 6  # 360 / 60

    #clock_text = time.strftime('%M')
    #clock_text = '%02d' % minutes
    #clock_text = '%d' % minutes
    #
    #clock_text = time.strftime('%H')
    clock_text = '%02d' % hours  # TODO single digit or 2 and display center
    clock_text = '%d' % hours  # TODO single digit or 2 and display center
    # https://pillow.readthedocs.io/en/stable/reference/ImageDraw.html#PIL.ImageDraw.ImageDraw.text
    # ImageDraw.text(xy, text, fill=None, font=None, anchor=None, spacing=4, align='left', direction=None, features=None, language=None, stroke_width=0, stroke_fill=None, embedded_color=False, font_size=None)

    # calc boundary and locatation each time for center - needed as precalc works for either single or double digits but not both (could pre-calc both..)
    try:
        clock_font_box = clock_font.getbbox(clock_text)  # with older PIL ('7.0.0') not available; AttributeError: 'FreeTypeFont' object has no attribute 'getbbox'. Fine with Pillow PIL.__version__ == 11.1.0
        clock_font_width, clock_font_height = clock_font_box[2], clock_font_box[3]
        print('clock_font_box %r' % (clock_font_box,))
    except :
        clock_font_width, clock_font_height = clock_font.getsize('00')

    print('clock_font sizes %r' % ((clock_font_width, clock_font_height),))

    text_pos = (0, 0)
    text_pos = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)  # FIXME close enough for initial version
    text_pos = ((SCREEN_WIDTH - clock_font_width) // 2, (SCREEN_HEIGHT - clock_font_height) // 2)  # WIP clock_font_width, clock_font_height
    draw.text(text_pos, clock_text, font=clock_font, fill=digit_color, align='center')


    # https://pillow.readthedocs.io/en/stable/reference/ImageDraw.html#PIL.ImageDraw.ImageDraw.ellipse
    # ImageDraw.ellipse(xy, fill=None, outline=None, width=1)

    # https://pillow.readthedocs.io/en/stable/reference/ImageDraw.html#PIL.ImageDraw.ImageDraw.arc
    # ImageDraw.arc(xy, start, end, fill=None, width=0)[source]
    #  Angles are measured from 3 o'clock, increasing clockwise
    # FIXME hard coded coordinates
    draw.arc(circle_box, -90, degree-90, fill=arc_color, width=arc_width)

    # TODO (based on format) convert image to 4-bit palette indexed image
    # this file should be generated using a tool like:
    #  * https://github.com/clach04/cyd_clocks/blob/main/image_converter.py
    #  * https://github.com/peterhinch/micropython-nano-gui/blob/master/img_cvt.py
    if format == '4bitbin':  # FIXME use a variable rather than literal
        return convert_image(image)
    else:
        bufferedfileptr = FakeFile()
        if format in ('pbm', 'xbm'):
            #im = ImageOps.invert(image)  # TODO invert at end?  - error; NotImplementedError: mode P support coming soon
            #image = im.convert("1", dither=Image.FLOYDSTEINBERG)
            image = image.convert("1", dither=Image.FLOYDSTEINBERG)
            image = ImageOps.invert(image)
            if format == 'pbm':
                format = 'ppm'  # PIL will emit pbm, for 1-bit ppm. Will error if request pbm
        image.save(bufferedfileptr, format=format)
        return bufferedfileptr.getvalue()
    #image.show()

################################################

content_type_lookup = {
    'pbm': 'image/x-portable-bitmap',  # convention, not standard. Also see image/x-portable-anymap - https://netpbm.sourceforge.net/doc/pbm.html
    'png': 'image/png',
    '4bitbin': 'application/octet-stream',  # TODO consider application/x-binary or custom to this app; application/x-bms, application/x-bitmap-server, etc.
}

# TODO version, and include in header response

def application(environ, start_response):
    # DEBUG
    for key in environ:
        if key.startswith('HTTP_'):  # TODO potentially startswith 'wsgi' as well
            # TODO remove leading 'HTTP_'?
            print('http header ' + key + ' = ' + repr(environ[key]))

    path_info = environ['PATH_INFO']
    print('%r' % (path_info,))
    if path_info != '/':
        return not_found(environ, start_response)

    # Determine image type to return
    # TODO check device MAC/id and use that for lookup, for now use info from client heuristic
    # FIXME/TODO remove string literals below and replace with constants
    image_type = '4bitbin'  # default
    HTTP_ACCEPT = environ.get('HTTP_ACCEPT', '')
    HTTP_USER_AGENT = environ.get('HTTP_USER_AGENT', '')
    if environ.get('HTTP__BPP'):
        bpp = int(environ.get('HTTP__BPP'))  # TODO error handling
        if bpp == 1:
            image_type = 'pbm'
        elif bpp == 4:
            image_type = '4bitbin'  # nano-gui color
        else:
            raise NotImplementedError('bit depth %r' % bpp)
    elif HTTP_ACCEPT == '*/*' or 'image/apng' in HTTP_ACCEPT or HTTP_USER_AGENT.startswith('curl') or HTTP_USER_AGENT.startswith('Mozilla'):
       image_type = 'png'


    # TODO handle errors and return something suitable to client
    #data, content_type = generate_image(format='png'), 'image/png'
    #data, content_type = generate_image(format='4bitbin'), 'application/octet-stream'
    data = generate_image(format=image_type, screen_width=environ.get('HTTP_WIDTH'), screen_height=environ.get('HTTP_HEIGHT'))  # TODO support image/device override in (server side) config (based on HTTP_ID)
    content_type = content_type_lookup[image_type]

    start_response('200 OK', [
        ('Content-type', content_type),
        ('Content-Length', str(len(data))),
        # TODO image meta data https://github.com/clach04/bitmap_server/issues/7
    ])
    return [data]
    


def main(argv=None):
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

if __name__ == "__main__":
    sys.exit(main())
