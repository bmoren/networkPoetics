# networkPoetics - MicroPython Captive Portal

A captive portal implementation for Raspberry Pi Pico W using MicroPython and the Phew library.

## Features

- **WiFi Access Point** - Creates "networkPoetics" network
- **DNS Redirection** - Captures all DNS queries and redirects to portal
- **Captive Portal Detection** - Automatically triggers portal popup on iOS, Android, and Windows
- **Custom HTML Serving** - Serve your own HTML content
- **Live Development** - Use `mpremote mount` for instant file updates

## Hardware Requirements

- Raspberry Pi Pico W (or Pico W2)
- USB cable for programming

## Software Requirements

- MicroPython v1.20+ for Pico W
- mpremote (for file management)
- Phew library (captive portal framework)

## Installation

### 1. Flash MicroPython

Download the latest MicroPython firmware for Pico W from [micropython.org](https://micropython.org/download/rp2-pico-w/)

1. Hold the **BOOTSEL** button on your Pico W
2. Connect USB cable to your computer
3. Pico appears as **RPI-RP2** USB drive
4. Drag the `.uf2` firmware file to the drive
5. Pico will automatically reboot with MicroPython

### 2. Install mpremote

```bash
pip install mpremote
```

### 3. Install Phew Library

```bash
mpremote mip install github:pimoroni/phew
```

### 4. Upload Files to Pico W

**Option A: For Production (files stored on Pico)**
```bash
cd /path/to/networkPoetics
mpremote cp main.py :main.py
mpremote cp index.html :index.html
```

**Option B: For Development (files served from PC - RECOMMENDED)**
```bash
cd /path/to/networkPoetics
mpremote mount .
```

This mounts your local directory as `/remote` on the Pico. Edit files locally and they're instantly accessible!

## Usage

### Running the Captive Portal

The portal starts automatically when `main.py` is present on the Pico W.

**Manual start via mpremote:**
```bash
mpremote run main.py
```

**With mounted filesystem (development):**
```bash
mpremote mount . + run main.py
```

### Connecting to the Portal

1. Look for WiFi network **"networkPoetics"**
2. Connect using password: **"poetics123"**
3. Captive portal should appear automatically
4. If not, open browser and navigate to any website

### Development Workflow

1. **Edit files locally** - Modify `index.html`, `style.css`, etc. in your project directory
2. **Run with mount** - `mpremote mount . + run main.py`
3. **Test in browser** - Connect to WiFi and reload page to see changes
4. **Iterate** - No need to transfer files or restart!

## Configuration

Edit `main.py` to customize:

```python
# Access Point Configuration
AP_SSID = "networkPoetics"       # WiFi network name
AP_PASSWORD = "poetics123"       # WiFi password (min 8 characters)
```

## File Structure

```
networkPoetics/
├── main.py           # Main MicroPython application
├── index.html        # Portal HTML content
├── code.py           # Original CircuitPython implementation (reference)
└── README.md         # This file
```

**On Pico W after installation:**
```
/ (root)
├── main.py           # Runs automatically on boot
├── index.html        # HTML content (optional, can use mpremote mount)
└── lib/
    └── phew/         # Phew library files
```

## Troubleshooting

### Portal doesn't appear automatically

Some devices require manual navigation:
- Open browser and go to `http://192.168.4.1`
- Try visiting any HTTP (not HTTPS) website
- Check device WiFi settings for "Sign in to network" notification

### Can't connect to WiFi

- Verify password is at least 8 characters
- Some devices won't connect to WPA2 networks without internet
- Try forgetting and reconnecting to the network

### HTML changes not reflected

If using `mpremote mount`:
- Ensure mount command is still running
- Check that `main.py` tries `/remote/index.html` first
- Reload the page in browser

If using copied files:
- Files are cached on boot, restart Pico W: `mpremote reset`
- Or modify main.py to reload HTML on each request

### DNS not working

- Check that Phew library is installed: `mpremote ls /lib/phew`
- Verify console shows "DNS server routing all queries to..."
- Some devices cache DNS, forget WiFi network and reconnect

### Memory issues

Check available memory:
```python
import gc
gc.collect()
print(gc.mem_free())  # Should be > 100000 bytes
```

## Comparison: CircuitPython vs MicroPython

| Feature | CircuitPython (code.py) | MicroPython (main.py) |
|---------|------------------------|----------------------|
| **DNS Response** | 70-80% success (broadcast) | 99% success (direct) |
| **Code Lines** | ~260 lines | ~80 lines |
| **CPU Usage** | ~15-20% (polling) | ~5-10% (async) |
| **Library Support** | Custom implementation | Phew library |
| **Development** | USB drive auto-mount | mpremote mount |

## Advanced Usage

### Hot-Reloading HTML

Modify the `index()` route in `main.py` to reload HTML on every request:

```python
@server.route("/", methods=["GET"])
def index(request):
    # Reload from disk each time
    for path in ["/remote/index.html", "index.html"]:
        try:
            with open(path, "r") as f:
                content = f.read()
            return content, 200, {"Content-Type": "text/html; charset=utf-8"}
        except:
            continue
    return "Error loading content", 500
```

### Serving Static Assets

Place CSS, JS, or images in your project directory and add routes:

```python
@server.route("/style.css", methods=["GET"])
def serve_css(request):
    with open("/remote/style.css", "r") as f:
        return f.read(), 200, {"Content-Type": "text/css"}
```

### Adding Custom Routes

```python
@server.route("/api/status", methods=["GET"])
def status(request):
    import gc
    data = {
        "memory": gc.mem_free(),
        "clients": len(ap.status('stations'))
    }
    return str(data), 200, {"Content-Type": "application/json"}
```

## Resources

- [MicroPython Documentation](https://docs.micropython.org/)
- [Phew Library (GitHub)](https://github.com/pimoroni/phew)
- [Pico W Documentation](https://www.raspberrypi.com/documentation/microcontrollers/raspberry-pi-pico.html)
- [mpremote Documentation](https://docs.micropython.org/en/latest/reference/mpremote.html)

## License

This project is open source. Feel free to modify and use for your own poetic network experiments.

## Credits

- Built with [MicroPython](https://micropython.org/)
- Uses [Phew](https://github.com/pimoroni/phew) by Pimoroni
- Inspired by network poetry and captive portal art projects
