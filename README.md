# BitMap Server (BMS)

Work-in-progress.

Serve (raw) bitmaps from a webserver:

    # generate some_file.bin  using https://github.com/clach04/cyd_clocks/blob/main/image_converter.py
    env BMS_BIN_FILE=some_file.bin LISTEN_PORT=1299 python bitmap_server.py

Serve (PNG) bitmap images of current time:

    python bitmap_server_pil_clock_rota_minute.py

Test cURL client:

    curl -v -H "Width: 100" -H "Height: 200" http://localhost:8080 --output test.png

## Optional setup


    pip install pillow
    pip install Werkzeug
