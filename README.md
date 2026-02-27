 # networkPoetics

A WiFi captive portal for Raspberry Pi Pico W 2. When devices connect to the network it creates, a portal page appears automatically — serving whatever HTML, images, and media you put on it.

Built for network poetry, art installations, and offline creative experiences.

---

## Setup

### 1. Flash MicroPython firmware

- Download the latest `.uf2` from https://micropython.org/download/RPI_PICO2_W/
- Hold **BOOTSEL** button on the Pico, plug in USB, then release BOOTSEL
- Pico appears as **RPI-RP2** drive — drag the `.uf2` file onto it
- Pico reboots automatically (drive disappears — this is normal)

### 2. Install mpremote

```bash
brew install mpremote     # macOS
pip3 install mpremote     # Linux
pip install mpremote      # Windows
```

### 3. Install Phew library (onto the Pico)

```bash
mpremote mip install github:pimoroni/phew
```

**If you get an SSL certificate error on macOS**, run this instead:
```bash
SSL_CERT_FILE=$(python3 -c "import certifi; print(certifi.where())") mpremote mip install github:pimoroni/phew
```
(Install certifi first if needed: `pip3 install certifi`)

**Manual install fallback** — download the Phew repo from GitHub as a zip, extract it, then:
```bash
mpremote mkdir :lib
mpremote mkdir :lib/phew
mpremote cp phew/__init__.py :lib/phew/__init__.py
mpremote cp phew/dns.py :lib/phew/dns.py
mpremote cp phew/logging.py :lib/phew/logging.py
mpremote cp phew/server.py :lib/phew/server.py
```

Verify:
```bash
mpremote ls :lib/phew
```

### 4. Upload the portal

```bash
cd networkPoetics_micropython
mpremote cp main.py :main.py
mpremote cp index.html :index.html

# Copy media from folder (if you have one)
#first make the folder
mpremote mkdir :media
#then copy each file (must do each one, one by one.)
mpremote cp media/photo.jpg :media/photo.jpg

```

The Pico auto-runs `main.py` on every boot — no PC needed once deployed.

---

## Connect

1. Connect to WiFi: **networkPoetics** / password: **poetics123**
2. Captive portal appears automatically
3. If it doesn't auto-appear: open browser to `http://192.168.4.1`

## Development workflow (temporary viewing)

Edit files on your computer and see changes instantly without copying to the Pico.

```bash
cd networkPoetics_micropython
mpremote mount . + run main.py
```

The `+` is important — it mounts your local folder and starts the server together. `mount .` alone does not start the portal.

- Edit `index.html` in your editor, refresh browser — changes appear immediately
- Add files to `media/` — accessible at `http://192.168.4.1/media/filename`
- Press `Ctrl+C` to stop

## Deployment (for final / standalone use)

Copy files to the Pico for standalone operation (no PC needed).

```bash
# Copy HTML
mpremote cp index.html :index.html

# Copy media folder
mpremote mkdir :media
mpremote cp media/photo.jpg :media/photo.jpg
# repeat for each file

# Verify
mpremote ls
```

Disconnect USB — Pico runs from any USB power source.

## Customization of WiFi name or password

Edit `networkPoetics_micropython/main.py`:

```python
AP_SSID     = "yourNetworkName"
AP_PASSWORD = "yourPassword"
```

To run as an open network with no password:

```python
AP_SSID     = "yourNetworkName"
AP_PASSWORD = None
```

Upload and press RESET on the Pico:

```bash
mpremote cp main.py :main.py
```

## Additional Files for expanded projects
### Multiple pages

```bash
mpremote cp about.html :about.html
```

Link between pages in HTML:

```html
<a href="/about.html">About</a>
```

### Add media

Reference files in your HTML using root-relative paths:

```html
<img src="/media/photo.jpg">
<audio controls src="/media/song.mp3"></audio>
<video controls src="/media/clip.mp4"></video>
```

Supported types: JPEG, PNG, GIF, WebP, SVG, MP4, WebM, MP3, WAV, CSS, JS


## File management reference

```bash
# List files on Pico
mpremote ls
mpremote ls :media

# Copy a file
mpremote cp file.html :file.html

# Copy an entire folder
# Note: destination must not already exist — if it does, delete it first:
mpremote exec "
import os
def rmrf(p):
    for n in os.listdir(p):
        f = p+'/'+n
        try: rmrf(f)
        except: pass
        try: os.remove(f)
        except: os.rmdir(f)
rmrf('/media')
os.rmdir('/media')
"

#batch copy files to an existing folder on the pico
for f in media/*; do mpremote cp "$f" ":media/$(basename $f)"; done

# Create a directory
mpremote mkdir :foldername

# Delete a file
mpremote rm :file.html

# Check free space (~1.4 MB total)
mpremote exec "import os; s = os.statvfs('/'); print('Free:', s[0]*s[3]//1024, 'KB'); print('Total:', s[0]*s[2]//1024, 'KB')"

# View serial output / REPL
mpremote
```

## Troubleshooting

**Device not found**
- Check the USB cable supports data (not charge-only)
- Run `mpremote connect list` to see connected devices
- Try specifying port: `mpremote connect /dev/cu.usbmodem1234 ls`

**Portal doesn't auto-appear**
- Navigate manually to `http://192.168.4.1`
- Try airplane mode on, then WiFi on (clears DNS cache)

**File not loading**
- Check it exists: `mpremote ls :media`
- Paths are case-sensitive and must start with `/`
- Access directly to test: `http://192.168.4.1/media/photo.jpg`

**Out of space**
- Pico W has ~1.4 MB for files; keep images compressed (WebP or small JPEG), avoid video
- Remove files: `mpremote rm :large_file.mp4`

## Adding an SD card (expanded storage)

The Pico 2W has ~1.4 MB of usable flash. A microSD card expands this to gigabytes, making it practical to serve large images, audio, and video.

### 1. What to buy

Any **SPI microSD breakout board** works. Search for "SPI SD card module" or "microSD breakout" — these are widely available for a few dollars. Common options:

- Generic SPI SD card module (cheapest, widely available)
- Adafruit MicroSD SPI Breakout (reliable, well-documented)
- SparkFun MicroSD Transflash Breakout

You'll also need short jumper wires (female-to-male or female-to-female depending on your breakout).

### 2. Wiring

Connect the SD module to the Pico 2W using SPI0:

| SD module pin | Pico 2W pin | Physical pin |
|---|---|---|
| VCC / 3V3 | 3.3V | Pin 36 |
| GND | GND | Pin 38 |
| SCK / CLK | GP2 | Pin 4 |
| MOSI / SDI / DI | GP3 | Pin 5 |
| MISO / SDO / DO | GP4 | Pin 6 |
| CS / CE | GP5 | Pin 7 |

> Pin labels vary by breakout board — VCC/3V3, MOSI/SDI/DI, and MISO/SDO/DO are the same signals with different names.

> **Important:** Use the **3.3V** pin, not 5V. Most SD modules include a voltage regulator, but always check your specific board's datasheet.

### 3. Format the SD card

Format as **FAT32**. Most cards ship pre-formatted as FAT32 — if yours isn't, format it on your computer before use. Cards up to 32 GB work reliably; larger cards may need exFAT which is not supported.

### 4. Install the SD driver onto the Pico

```bash
mpremote mip install sdcard
```

Verify:
```bash
mpremote ls :lib
# should show: sdcard.py (or sdcard/)
```

### 5. Upload updated main.py

```bash
mpremote cp main.py :main.py
```

Reset the Pico. You should see `SD card mounted at /sd` in the serial output if wired correctly.

Check serial output:
```bash
mpremote
```

### 6. Put files on the SD card

Connect the SD card to your computer and copy files directly in Finder or Explorer. Use the same folder structure as you would on the Pico flash:

```
SD card root/
├── index.html          (optional — overrides flash version)
├── media/
│   ├── photo.jpg
│   ├── audio.mp3
│   └── video.mp4
└── css/
    └── style.css
```

Eject the SD card, insert it into the module, and power the Pico. Your HTML doesn't need to change — `/media/photo.jpg` works whether the file is on the SD card or Pico flash.

**File serving priority:** development mount → SD card → Pico flash

If no SD card is detected at boot the portal continues normally using flash storage only.

### Performance expectations

SD card files are served over SPI (a slow serial bus) through MicroPython, then over WiFi. The practical throughput ceiling is roughly **300–400 KB/s** — set by the Pico W's WiFi stack, not the card itself.

What this means in practice:

| Content | Works well? | Notes |
|---|---|---|
| HTML / CSS / JS | ✅ | Tiny files, instant |
| Images (JPEG/WebP) | ✅ | Keep under ~2 MB |
| Audio (MP3) | ✅ | Keep bitrate under 256 kbps |
| Audio (WAV) | ⚠️ | Uncompressed — 44.1kHz stereo = 176 KB/s, just fits |
| Video (MP4) | ⚠️ | Must be encoded at low bitrate — see below |

**Preparing video for the Pico W**

Video must be encoded at a low enough bitrate to stream in real time. Anything above ~2.5 Mbps (300 KB/s) will play in slow motion or stall.

Re-encode with ffmpeg on your Mac:

```bash
ffmpeg -i input.mp4 -c:v libx264 -b:v 1200k -c:a aac -b:a 96k -movflags +faststart output.mp4
```

- `-b:v 1200k` — 1.2 Mbps video (adjust down if still slow)
- `-b:a 96k` — 96 kbps audio
- `-movflags +faststart` — moves metadata to the front so playback starts before the full file downloads

Check the bitrate of any existing file:

```bash
ffprobe -v quiet -show_entries format=bit_rate -of default=noprint_wrappers=1 yourfile.mp4
```

**Keep wires short.** SPI runs at 20 MHz — longer jumper wires introduce noise and can cause read errors or card mount failures at boot.

**The SD card must be inserted before power-on.** It is not hot-swappable; the driver only initialises once at boot.

### Troubleshooting SD card

**`No SD card (continuing without)`** at boot
- Check wiring — especially MOSI/MISO aren't swapped (most common cause)
- Verify VCC is connected to 3.3V not 5V
- Try a different SD card (some cards are finicky at boot)
- Confirm card is FAT32 formatted
- If it worked before and stopped, try shorter jumper wires

**`timeout waiting for v2 card`** in serial output
- MOSI and MISO are likely swapped — swap those two wires and try again
- Try a different SD card

**Files on SD card not loading**
- Check the card is properly inserted and seated
- Verify file paths match exactly (case-sensitive)
- Check `mpremote` serial output — it prints which path each file was served from

**Video plays in slow motion / audio sounds slow**
- The video bitrate is too high for the Pico W's WiFi throughput
- Re-encode at a lower bitrate using the ffmpeg command above

## Technical

- **Platform:** Raspberry Pi Pico W / MicroPython
- **Libraries:** Phew (Pimoroni) for DNS + AP; raw uasyncio for HTTP
- **WiFi:** Access Point mode at 192.168.4.1
- **DNS:** UDP port 53, catchall redirects all queries to the portal
- **HTTP:** Async server on port 80
- **Storage:** LittleFS, ~1.4 MB usable; microSD via SPI (FAT32, optional)
- **Concurrent connections:** 4
