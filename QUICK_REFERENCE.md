# Quick Reference Card

## One-Line Setup
```bash
pip install mpremote && mpremote mip install github:pimoroni/phew
```

## One-Line Run (Development)
```bash
mpremote mount . + run main.py
```

## One-Line Deploy (Production)
```bash
mpremote cp main.py :main.py && mpremote cp index.html :index.html && mpremote reset
```

---

## WiFi Connection
- **SSID:** networkPoetics
- **Password:** poetics123
- **IP:** 192.168.4.1

---

## mpremote Cheatsheet

### File Management
```bash
mpremote ls                    # List files on Pico
mpremote cp file.py :file.py   # Copy to Pico
mpremote rm file.py            # Delete from Pico
mpremote mount .               # Mount local dir as /remote
```

### Execution
```bash
mpremote run main.py           # Run file
mpremote reset                 # Soft reset
mpremote repl                  # Enter REPL (Ctrl-X to exit)
mpremote exec "print('hi')"    # Execute Python
```

### Combined Commands (use +)
```bash
mpremote mount . + run main.py
mpremote cp main.py :main.py + reset
```

---

## File Locations

### Development (mpremote mount)
- **On PC:** `/Users/bmoren/Desktop/networkPoetics/index.html`
- **On Pico:** `/remote/index.html`
- Edit files on PC → Changes live instantly

### Production (copied files)
- **On Pico:** `/index.html`
- Files permanent on Pico's flash
- Need `mpremote reset` after changes

---

## Code Patterns

### Add Route
```python
@server.route("/page", methods=["GET"])
def my_page(request):
    return "<h1>Hello</h1>", 200, {"Content-Type": "text/html"}
```

### Serve File
```python
@server.route("/style.css", methods=["GET"])
def css(request):
    with open("/remote/style.css") as f:
        return f.read(), 200, {"Content-Type": "text/css"}
```

### API Endpoint
```python
@server.route("/api/data", methods=["GET"])
def api(request):
    return '{"status": "ok"}', 200, {"Content-Type": "application/json"}
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| No module 'phew' | `mpremote mip install github:pimoroni/phew` |
| Can't find Pico | Reconnect USB, try different port/cable |
| Changes not showing | Reload browser (Ctrl+R) or `mpremote reset` |
| Portal doesn't pop up | Open browser to http://192.168.4.1 |
| WiFi won't connect | Password must be 8+ chars |
| Memory error | `import gc; gc.collect()` |

---

## REPL Commands

```bash
mpremote repl
```

```python
# Check connection
import network
ap = network.WLAN(network.AP_IF)
print(ap.active())        # Should be True
print(ap.ifconfig())      # IP config

# Memory check
import gc
gc.collect()
print(gc.mem_free())      # Free memory in bytes

# Stop program
# Ctrl-C

# Soft reboot
# Ctrl-D

# Exit REPL
# Ctrl-X
```

---

## File Structure

### Minimal Setup
```
/ (Pico root)
├── main.py          # Required
└── lib/phew/        # Required (installed via mip)
```

### With HTML
```
/ (Pico root)
├── main.py
├── index.html
└── lib/phew/
```

### Full Setup
```
/ (Pico root)
├── main.py
├── index.html
├── style.css
├── script.js
└── lib/phew/
```

---

## Common Workflows

### Edit HTML and Test
```bash
# Terminal 1
mpremote mount . + run main.py

# Terminal 2
code index.html
# Save → Reload browser → See changes
```

### Deploy to Pico
```bash
mpremote cp main.py :main.py
mpremote cp index.html :index.html
mpremote reset
# Disconnect USB - runs standalone
```

### Update Phew Library
```bash
mpremote mip install --force github:pimoroni/phew
```

### View Logs
```bash
mpremote run main.py
# See all print() output in terminal
```

---

## URLs

| URL | Purpose |
|-----|---------|
| http://192.168.4.1 | Main portal page |
| http://192.168.4.1/api/status | API endpoint (if using example_with_static_files.py) |
| http://192.168.4.1/style.css | CSS file (if served) |

---

## Configuration

### Change WiFi Network
```python
# In main.py
AP_SSID = "YourNetwork"
AP_PASSWORD = "password123"  # Min 8 chars
```

### Change IP Address
```python
# After: ap = access_point(...)
ap.ifconfig(('192.168.5.1', '255.255.255.0', '192.168.5.1', '8.8.8.8'))
ip = ap.ifconfig()[0]
```

---

## Performance

| Metric | Value |
|--------|-------|
| DNS Success | 99% |
| Connection Latency | 10-30ms |
| CPU Usage | 5-10% |
| Memory Usage | ~60KB |
| Max Clients | 4 simultaneous |
| Code Size | ~80 lines |

---

## Key Files

| File | Purpose |
|------|---------|
| main.py | Core portal (start here) |
| index.html | Portal HTML page |
| example_with_static_files.py | Extended example |
| test.html | Interactive test page |
| README.md | Full documentation |
| SETUP_GUIDE.md | Setup instructions |

---

## Emergency Recovery

### Reflash MicroPython
1. Hold BOOTSEL button
2. Connect USB
3. Drag .uf2 firmware to RPI-RP2 drive

### Clear All Files
```bash
mpremote fs rm :main.py
mpremote fs rm :index.html
```

### Factory Reset
Reflash MicroPython firmware (above) - clears everything

---

## Links

- MicroPython: https://micropython.org/
- Phew Library: https://github.com/pimoroni/phew
- Pico W Docs: https://www.raspberrypi.com/documentation/
- mpremote Guide: https://docs.micropython.org/en/latest/reference/mpremote.html

---

## Quick Test

```bash
# 1. Install
pip install mpremote
mpremote mip install github:pimoroni/phew

# 2. Run
cd /Users/bmoren/Desktop/networkPoetics
mpremote mount . + run main.py

# 3. Connect
# WiFi: networkPoetics
# Password: poetics123
# Browser: Opens automatically!
```

---

**Print this card for reference while working!**
