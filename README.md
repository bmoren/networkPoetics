# networkPoetics

A WiFi captive portal for Raspberry Pi Pico W. When devices connect to the network it creates, a portal page appears automatically — serving whatever HTML, images, and media you put on it.

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

Verify:
```bash
mpremote ls :lib/phew
```

### 4. Upload the portal

```bash
cd networkPoetics_micropython
mpremote cp main.py :main.py
mpremote cp index.html :index.html

# Copy media folder (if you have one)
mpremote mkdir :media
mpremote cp -r media :media
```

The Pico auto-runs `main.py` on every boot — no PC needed once deployed.

---

## Connect

1. Connect to WiFi: **networkPoetics** / password: **poetics123**
2. Captive portal appears automatically
3. If it doesn't auto-appear: open browser to `http://192.168.4.1`

---

## Development workflow

Edit files on your computer and see changes instantly without copying to the Pico.

```bash
cd networkPoetics_micropython
mpremote mount . + run main.py
```

The `+` is important — it mounts your local folder and starts the server together. `mount .` alone does not start the portal.

- Edit `index.html` in your editor, refresh browser — changes appear immediately
- Add files to `media/` — accessible at `http://192.168.4.1/media/filename`
- Press `Ctrl+C` to stop

---

## Deployment (standalone)

Copy files to the Pico for standalone operation (no PC needed).

```bash
# Copy HTML
mpremote cp index.html :index.html

# Copy media folder
mpremote mkdir :media
mpremote cp -r media :media

# Verify
mpremote ls
```

Disconnect USB — Pico runs from any USB power source.

---

## Customization

### Change WiFi name or password

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

---

## File management reference

```bash
# List files on Pico
mpremote ls
mpremote ls :media

# Copy a file
mpremote cp file.html :file.html

# Copy an entire folder
mpremote mkdir :media
mpremote cp -r media :media

# Create a directory
mpremote mkdir :foldername

# Delete a file
mpremote rm :file.html

# Check free space (~1.4 MB total)
mpremote exec "import os; s = os.statvfs('/'); print('Free:', s[0]*s[3]//1024, 'KB'); print('Total:', s[0]*s[2]//1024, 'KB')"

# View serial output / REPL
mpremote
```

---

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

---

## Technical

- **Platform:** Raspberry Pi Pico W / MicroPython
- **Libraries:** Phew (Pimoroni) for DNS + AP; raw uasyncio for HTTP
- **WiFi:** Access Point mode at 192.168.4.1
- **DNS:** UDP port 53, catchall redirects all queries to the portal
- **HTTP:** Async server on port 80
- **Storage:** LittleFS, ~1.4 MB usable
- **Concurrent connections:** 4
