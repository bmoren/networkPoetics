# Network Poetics - MicroPython Captive Portal

**99% DNS reliability** | **Easy file management** | **Media support**

A captive portal for Raspberry Pi Pico W with robust DNS and simple file management.

## Quick Start

**New to this project?** → See [../GETTING_STARTED.md](../GETTING_STARTED.md) for complete setup instructions.

## What's Included

### Core Files

- **`main.py`** - Captive portal application
  - WiFi Access Point configuration
  - DNS catchall server (192.168.4.1)
  - HTTP server with static file serving
  - Captive portal detection for iOS/Android/Windows

- **`index.html`** - Default portal page
  - Responsive design
  - Network poetry theme
  - Customizable starting point

- **`index_with_media.html`** - Media gallery example
  - Image gallery layout
  - Video and audio player examples
  - File organization guide

### Documentation

- **`MPREMOTE_GUIDE.md`** - Complete mpremote reference
  - File upload/download commands
  - Live mounting workflow
  - Advanced usage examples

## Installation (Quick Version)

```bash
# 1. Flash MicroPython firmware (one time)
#    Download from https://micropython.org/download/RPI_PICO_W/
#    Hold BOOTSEL, plug USB, drag .uf2 file to RPI-RP2 drive

# 2. Install mpremote
pip3 install mpremote

# 3. Upload portal code
cd networkPoetics_micropython
mpremote cp main.py :main.py
mpremote cp index.html :index.html

# 4. Test it
mpremote run main.py
# Connect to WiFi: networkPoetics / poetics123
# Portal appears at http://192.168.4.1
```

## Daily Workflow

### Development (Live Editing)

```bash
# Edit files on your computer, see changes instantly
mpremote mount .

# Edit index.html in your editor
# Changes appear immediately when you refresh browser
# Press Ctrl+C when done
```

### Deployment (Standalone)

```bash
# Copy files to Pico for standalone operation
mpremote cp index.html :index.html
mpremote cp -r media :media

# Disconnect USB - Pico runs standalone
```

## Configuration

Edit `main.py` to change WiFi settings:

```python
AP_SSID = "networkPoetics"      # Change WiFi name
AP_PASSWORD = "poetics123"       # Change password
```

Upload the modified file:

```bash
mpremote cp main.py :main.py
```

Press RESET button on Pico to apply changes.

## File Organization

```
/ (root on Pico)
├── main.py              # Portal application
├── index.html           # Homepage
├── media/              # Media files
│   ├── images/
│   │   └── photo.jpg
│   ├── videos/
│   │   └── clip.mp4
│   └── audio/
│       └── song.mp3
├── css/                # Stylesheets
│   └── style.css
└── js/                 # JavaScript
    └── script.js
```

## Adding Files

```bash
# Create directories
mpremote mkdir :media
mpremote mkdir :css
mpremote mkdir :js

# Upload files
mpremote cp style.css :css/style.css
mpremote cp photo.jpg :media/photo.jpg
mpremote cp video.mp4 :media/video.mp4

# Upload entire directory
mpremote cp -r media :media

# List files
mpremote ls
mpremote ls :media
```

## Supported File Types

**Web Content:**
- HTML, CSS, JavaScript
- JSON, TXT

**Images:**
- JPEG, PNG, GIF, SVG, WebP

**Video:**
- MP4, WebM

**Audio:**
- MP3, WAV

## Features

### Captive Portal Detection
Automatically handles detection requests from:
- iOS (`/hotspot-detect.html`)
- Android (`/generate_204`)
- Windows (`/connecttest.txt`)

### DNS Catchall
All DNS queries redirect to 192.168.4.1 (99% reliability)

### File Fallback
- Tries `/remote/` first (mpremote mount)
- Falls back to local filesystem
- Enables live editing during development

### MIME Type Detection
Automatic content-type headers based on file extension

## Troubleshooting

### Portal doesn't auto-appear
```bash
# Manually navigate to:
http://192.168.4.1
```

### Can't connect to Pico
```bash
# Check connection
mpremote connect list

# Try connecting again
mpremote
```

### File not found
```bash
# Check what's on the Pico
mpremote ls

# File paths must start with /
# Correct: http://192.168.4.1/media/photo.jpg
```

### Out of space
```bash
# Check space
mpremote df

# Remove files
mpremote rm :large_file.mp4
```

## Technical Details

**Platform:** MicroPython on Raspberry Pi Pico W
**Libraries:** Phew (included in MicroPython firmware)
**WiFi Mode:** Access Point (192.168.4.1)
**DNS:** UDP port 53, catchall to AP IP
**HTTP:** Async server on port 80
**Filesystem:** LittleFS (~1MB available)

## Why MicroPython?

✅ **Better DNS** - Proper socket.recvfrom() returns client addresses
✅ **Reliable** - 99% captive portal detection success
✅ **Phew library** - Built-in async server and DNS catchall
✅ **mpremote** - Live file editing during development

## Complete Documentation

- [GETTING_STARTED.md](../GETTING_STARTED.md) - Full setup guide
- [MPREMOTE_GUIDE.md](MPREMOTE_GUIDE.md) - mpremote reference
- [PLATFORM_COMPARISON.md](../PLATFORM_COMPARISON.md) - vs Arduino/CircuitPython

## Examples

See `index_with_media.html` for a complete example with:
- Image gallery
- Video player
- Audio player
- Organized file structure

---

**Ready to start?** → [GETTING_STARTED.md](../GETTING_STARTED.md)
