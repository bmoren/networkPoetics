# Quick Setup Guide

## 5-Minute Setup

### Step 1: Flash MicroPython (2 minutes)

1. Download firmware: https://micropython.org/download/rp2-pico-w/
2. Hold **BOOTSEL** button on Pico W
3. Connect USB cable
4. Drag `.uf2` file to **RPI-RP2** drive
5. Wait for reboot

### Step 2: Install Tools (1 minute)

```bash
pip install mpremote
```

### Step 3: Install Phew Library (1 minute)

```bash
mpremote mip install github:pimoroni/phew
```

### Step 4: Run the Portal (1 minute)

**For Development (files stay on your PC):**
```bash
cd /Users/bmoren/Desktop/networkPoetics
mpremote mount . + run main.py
```

**For Production (copy files to Pico):**
```bash
mpremote cp main.py :main.py
mpremote cp index.html :index.html
mpremote reset
```

### Step 5: Connect!

1. Find WiFi: **"networkPoetics"**
2. Password: **"poetics123"**
3. Portal appears automatically!

---

## Development Workflow

### Edit → Test → Repeat

```bash
# Terminal 1: Keep this running
cd /Users/bmoren/Desktop/networkPoetics
mpremote mount . + run main.py

# Terminal 2: Edit files
code index.html
# Save changes → Reload browser → See results instantly!
```

### Why Use mpremote mount?

- ✅ **No file transfers** - Files stay on your PC
- ✅ **Instant updates** - Edit and reload browser
- ✅ **Git-friendly** - Version control works normally
- ✅ **No flash wear** - Protects Pico's memory
- ✅ **Fast iteration** - Change → Test in seconds

---

## Common Commands

### Check if Pico is connected
```bash
mpremote ls
```

### See what's running
```bash
mpremote repl
# Press Ctrl-C to stop current program
# Press Ctrl-D to soft reboot
# Press Ctrl-X to exit REPL
```

### Copy a file to Pico
```bash
mpremote cp index.html :index.html
```

### Remove a file from Pico
```bash
mpremote rm index.html
```

### Reset the Pico
```bash
mpremote reset
```

### View serial output
```bash
mpremote repl
# Now run your program
# See all print() statements in real-time
```

---

## Customization Guide

### Change WiFi Network Name

Edit `main.py`:
```python
AP_SSID = "YourNetworkName"
AP_PASSWORD = "yourpassword"  # Min 8 characters
```

### Customize the Portal

Edit `index.html` - it's just HTML/CSS/JavaScript!

### Add Static Files

Create files in your project directory:
- `style.css` - Additional styles
- `script.js` - JavaScript functionality
- `logo.png` - Images (need to add route in main.py)

Add route in `main.py`:
```python
@server.route("/style.css", methods=["GET"])
def serve_css(request):
    with open("/remote/style.css", "r") as f:
        return f.read(), 200, {"Content-Type": "text/css"}
```

---

## Troubleshooting

### "No module named 'phew'"

Install Phew library:
```bash
mpremote mip install github:pimoroni/phew
```

### "Cannot find Pico"

1. Disconnect and reconnect USB
2. Try different USB port
3. Check USB cable (must support data, not just power)
4. Make sure no other program is using the serial port

### Changes not showing up

If using `mpremote mount`:
- Check mount command is still running in terminal
- Reload browser page (Cmd/Ctrl + R)
- Try hard reload (Cmd/Ctrl + Shift + R)

If files are copied to Pico:
- Need to restart: `mpremote reset`
- Or modify main.py to reload HTML each request

### Can't connect to WiFi

- Password must be 8+ characters
- Some phones require "internet" - this is normal for captive portal
- Try airplane mode → WiFi only
- Forget network and reconnect

### Portal doesn't pop up automatically

- Open browser manually
- Go to: `http://192.168.4.1`
- Check phone notifications for "Sign in to network"

---

## Next Steps

### Learn More

- Read [README.md](README.md) for full documentation
- Check [Phew examples](https://github.com/pimoroni/phew/tree/main/examples)
- Explore [MicroPython docs](https://docs.micropython.org/)

### Make It Yours

- Design custom HTML/CSS themes
- Add interactive JavaScript
- Create multi-page experiences
- Integrate sensors or LEDs
- Build network art installations

### Share Your Work

This is a network poetry experiment - make it your own!
