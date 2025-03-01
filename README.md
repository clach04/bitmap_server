# BitMap Server (BMS)

Work-in-progress.

Serve (raw) bitmaps from a webserver:

    # generate some_file.bin  using https://github.com/clach04/cyd_clocks/blob/main/image_converter.py
    env BMS_BIN_FILE=some_file.bin LISTEN_PORT=1299 python bitmap_server.py

Serve (PNG) bitmap images of current time:

    env LISTEN_PORT=1299 python3 bitmap_server_pil_clock_rota_minute.py
    python bitmap_server_pil_clock_rota_minute.py

Test cURL client:

    curl -v -H "Width: 100" -H "Height: 200"                http://localhost:8080 --output test.png
    curl -v -H "Width: 320" -H "Height: 240"                http://localhost:8080 --output test.png
    curl -v -H "Width: 320" -H "Height: 240" -H "_BPP: 4"   http://localhost:8080 --output test.bin
    curl -v -H "Width: 400" -H "Height: 300" -H "_BPP: 1"   http://localhost:8080 --output test.pbm

## Optional setup


    pip install pillow
    pip install Werkzeug
