# mpremote File Management Guide

## Overview

This version of networkPoetics uses **mpremote** for all file management. No admin panel - clean, simple, and efficient.

## Why mpremote?

✅ **Fast** - Direct USB connection, no network overhead
✅ **Simple** - Command-line tool, no web interface complexity
✅ **Reliable** - Standard Python tool, well-documented
✅ **Powerful** - Full filesystem access, scripting support
✅ **Secure** - No web-based upload vulnerabilities

## Quick Reference

### Essential Commands

```bash
# List files on Pico
mpremote ls

# Copy file to Pico
mpremote cp file.ext :file.ext

# Copy file to subdirectory
mpremote cp image.jpg :media/image.jpg

# Create directory
mpremote mkdir :media

# Delete file
mpremote rm :file.ext

# Run code (for testing)
mpremote run main.py

# Reset Pico
mpremote reset

# REPL access
mpremote repl
```

### Development Workflow

```bash
# Mount local directory (RECOMMENDED for development)
mpremote mount . + run main.py

# Your files appear at /remote/ on Pico
# Edit locally → Changes instant!
```

## Setup Instructions

### 1. Initial Deployment

```bash
# Navigate to project directory
cd /Users/bmoren/Desktop/networkPoetics

# Copy main application
mpremote cp main.py :main.py

# Copy HTML (optional, has fallback)
mpremote cp index.html :index.html

# Reset to start
mpremote reset
```

### 2. Create Directory Structure

```bash
# Create media directories
mpremote mkdir :media
mpremote mkdir :css
mpremote mkdir :js
```

### 3. Upload Media Files

```bash
# Upload images
mpremote cp photo1.jpg :media/photo1.jpg
mpremote cp photo2.jpg :media/photo2.jpg

# Upload videos
mpremote cp video.mp4 :media/video.mp4

# Upload audio
mpremote cp song.mp3 :media/song.mp3
```

### 4. Upload Web Assets

```bash
# CSS files
mpremote cp style.css :css/style.css

# JavaScript files
mpremote cp script.js :js/script.js
```

## Development Workflows

### Workflow 1: mpremote mount (BEST for development)

**Use Case:** Frequently editing HTML/CSS/JS

```bash
# Terminal 1: Keep this running
cd /Users/bmoren/Desktop/networkPoetics
mpremote mount . + run main.py

# Terminal 2: Edit files
code index.html
# Save changes → Reload browser → See instantly!
```

**Advantages:**
- ✅ No file copying needed
- ✅ Instant changes (just reload browser)
- ✅ Git works normally
- ✅ Use any editor

**How It Works:**
- Your local files appear at `/remote/` on Pico
- Code checks `/remote/index.html` first, then `index.html`
- Same for all media: `/remote/media/image.jpg` → `/media/image.jpg`

### Workflow 2: Copy Files (Production)

**Use Case:** Final deployment, standalone operation

```bash
# Copy all necessary files
mpremote cp main.py :main.py
mpremote cp index.html :index.html
mpremote mkdir :media
mpremote cp media/*.jpg :media/

# Reset and disconnect
mpremote reset

# Pico now runs standalone (no PC needed)
```

**Advantages:**
- ✅ Runs without PC connected
- ✅ Files permanently on Pico
- ✅ Good for installations

### Workflow 3: Hybrid Approach

**Use Case:** Development with large media files

```bash
# Copy large media files once (permanent)
mpremote mkdir :media
mpremote cp media/*.jpg :media/
mpremote cp media/*.mp4 :media/

# Use mount for HTML/CSS (live editing)
mpremote mount . + run main.py

# Edit HTML locally → Instant updates
# Media files already on Pico → Fast loading
```

## File Organization

### Recommended Structure

**On your PC:**
```
/Users/bmoren/Desktop/networkPoetics/
├── main.py              # Application code
├── index.html           # Portal HTML
├── media/               # Media files
│   ├── image1.jpg
│   ├── image2.jpg
│   ├── video.mp4
│   └── audio.mp3
├── css/                 # Stylesheets
│   └── style.css
└── js/                  # JavaScript
    └── script.js
```

**On Pico (production):**
```
/ (root)
├── main.py
├── index.html
├── media/
│   ├── image1.jpg
│   ├── image2.jpg
│   ├── video.mp4
│   └── audio.mp3
├── css/
│   └── style.css
├── js/
│   └── script.js
└── lib/
    └── phew/
```

**With mpremote mount (development):**
```
/ (root)
├── main.py              # On Pico
├── /remote/             # Your PC's files
│   ├── index.html
│   ├── media/
│   ├── css/
│   └── js/
└── lib/
    └── phew/
```

## HTML File References

### In Your HTML

```html
<!-- Images - works with both mounted and copied files -->
<img src="/media/image.jpg" alt="My Image">

<!-- Video -->
<video controls>
  <source src="/media/video.mp4" type="video/mp4">
</video>

<!-- Audio -->
<audio controls>
  <source src="/media/audio.mp3" type="audio/mpeg">
</audio>

<!-- CSS -->
<link rel="stylesheet" href="/css/style.css">

<!-- JavaScript -->
<script src="/js/script.js"></script>
```

### Path Resolution

Code automatically checks:
1. `/remote/media/image.jpg` (mpremote mount)
2. `/media/image.jpg` (copied file)
3. Fallback to HTML if not found

## Common Tasks

### Task: Update HTML Content

**During Development:**
```bash
# Terminal 1: Keep running
mpremote mount . + run main.py

# Terminal 2: Edit
code index.html
# Save → Reload browser
```

**In Production:**
```bash
# Edit locally
code index.html

# Upload
mpremote cp index.html :index.html

# No reset needed - will load on next page request
```

### Task: Add New Images

```bash
# Create directory if needed
mpremote mkdir :media

# Upload images
mpremote cp photo1.jpg :media/photo1.jpg
mpremote cp photo2.jpg :media/photo2.jpg
mpremote cp photo3.jpg :media/photo3.jpg

# Or batch upload all JPGs
for f in media/*.jpg; do
  mpremote cp "$f" ":media/$(basename $f)"
done
```

### Task: Replace Video

```bash
# Remove old video
mpremote rm :media/old_video.mp4

# Upload new video
mpremote cp new_video.mp4 :media/video.mp4
```

### Task: Update Stylesheet

```bash
# Upload CSS
mpremote cp style.css :css/style.css

# Visitors need to hard-refresh (Ctrl+Shift+R)
```

### Task: Check Available Space

```bash
mpremote repl
```

```python
import os
def get_free_space():
    stat = os.statvfs('/')
    block_size = stat[0]
    free_blocks = stat[3]
    return (free_blocks * block_size) / 1024  # KB

print(f"Free space: {get_free_space():.1f} KB")
# Ctrl-X to exit
```

### Task: Backup All Files

```bash
# Create backup directory
mkdir -p backup

# Download all files from Pico
mpremote fs cp :main.py backup/main.py
mpremote fs cp :index.html backup/index.html
# etc.

# Or use recursive copy (if available)
mpremote fs cp -r :/ backup/
```

## Troubleshooting

### "mpremote: command not found"

**Install mpremote:**
```bash
pip install mpremote
# or
pip3 install mpremote
```

### "Could not find a connected device"

**Check connection:**
- USB cable connected?
- Try different USB port
- Try different cable (must support data, not just power)
- Check: `ls /dev/tty.*` (macOS) or `ls /dev/ttyUSB*` (Linux)

**If multiple devices:**
```bash
mpremote connect /dev/tty.usbmodem1234 ls
```

### "No space left on device"

**Check space:**
```bash
mpremote repl
```
```python
import os
stat = os.statvfs('/')
free = (stat[3] * stat[0]) / 1024
print(f"{free:.1f} KB free")
```

**Free up space:**
```bash
# Remove unused files
mpremote rm :old_file.mp4

# List large files
mpremote exec "import os; [(f, os.stat(f)[6]) for f in os.listdir('/')]"
```

### Files not appearing in browser

**Check file exists:**
```bash
mpremote ls :media
```

**Check exact path:**
```bash
# In HTML: <img src="/media/image.jpg">
# Must exist at: /media/image.jpg (not /media/Image.jpg)
# Case-sensitive!
```

**Try accessing directly:**
```
http://192.168.4.1/media/image.jpg
```

**Check console:**
```bash
mpremote repl
# Run code, watch for "Serving..." messages
```

### mpremote mount not working

**Restart with mount:**
```bash
# Stop current code (Ctrl-C if running)
mpremote repl
# Ctrl-C to stop
# Ctrl-D to soft reboot
# Ctrl-X to exit

# Then mount
mpremote mount . + run main.py
```

**Check mount worked:**
```bash
# In another terminal
mpremote repl
```
```python
import os
print(os.listdir('/remote'))
# Should show your PC's files
```

## Advanced Usage

### Scripting with mpremote

```bash
#!/bin/bash
# deploy.sh - Deploy all files to Pico

echo "Creating directories..."
mpremote mkdir :media
mpremote mkdir :css
mpremote mkdir :js

echo "Uploading HTML..."
mpremote cp index.html :index.html

echo "Uploading media..."
for f in media/*.jpg; do
  echo "  $(basename $f)"
  mpremote cp "$f" ":media/$(basename $f)"
done

echo "Uploading CSS..."
mpremote cp css/style.css :css/style.css

echo "Uploading JS..."
mpremote cp js/script.js :js/script.js

echo "Resetting Pico..."
mpremote reset

echo "Done! Connect to WiFi: networkPoetics"
```

### Remote Commands

```bash
# Execute Python code
mpremote exec "print('Hello from Pico!')"

# Check WiFi status
mpremote exec "import network; ap = network.WLAN(network.AP_IF); print(ap.active())"

# List connected clients
mpremote exec "import network; print(network.WLAN(network.AP_IF).status('stations'))"
```

### Multiple Devices

```bash
# Connect to specific device
mpremote connect /dev/tty.usbmodem14201 ls

# Or set environment variable
export MPREMOTE_DEVICE=/dev/tty.usbmodem14201
mpremote ls
```

## File Size Recommendations

| File Type | Max Recommended | Notes |
|-----------|----------------|-------|
| **HTML** | 50KB | Keep lean |
| **CSS** | 30KB | Minify for production |
| **JavaScript** | 50KB | Minify for production |
| **Images (JPG)** | 200KB each | Compress before upload |
| **Audio (MP3)** | 3MB | Short clips only |
| **Video (MP4)** | Not recommended | Stream from external source |

**Total Storage:** ~1.4MB available

## Best Practices

### ✅ DO

- Use `mpremote mount` during development
- Copy files to Pico for production deployment
- Compress images before uploading
- Test locally before deploying
- Keep HTML/CSS/JS under 50KB each
- Use descriptive filenames (no spaces)

### ❌ DON'T

- Don't upload huge video files (>1MB)
- Don't use spaces in filenames
- Don't forget to create directories first
- Don't mix uppercase/lowercase randomly
- Don't upload while code is writing files

## Quick Cheat Sheet

```bash
# Setup
mpremote cp main.py :main.py
mpremote mkdir :media
mpremote cp index.html :index.html

# Development
mpremote mount . + run main.py

# Production
mpremote cp file.ext :file.ext
mpremote reset

# Maintenance
mpremote ls
mpremote rm :file.ext
mpremote repl

# Check status
mpremote exec "import os; print(os.listdir('/'))"
```

## Summary

**Use mpremote for:**
- ✅ All file uploads
- ✅ Development with live editing (mount)
- ✅ Production deployment (copy)
- ✅ File management and maintenance

**Advantages over web admin:**
- Faster (USB direct connection)
- More reliable (no network issues)
- Simpler (command-line, scriptable)
- Secure (no web upload vulnerabilities)
- Standard tool (well-documented)

---

For more information:
- [Official mpremote docs](https://docs.micropython.org/en/latest/reference/mpremote.html)
- [README.md](README.md) - Main documentation
- [index_with_media.html](index_with_media.html) - HTML example
