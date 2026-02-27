"""
Network Poetics Captive Portal
MicroPython - Raspberry Pi Pico W

Uses Phew for DNS catchall, raw asyncio for HTTP (full control over responses).

File Management:
- Development: mpremote mount . (files served live from your computer)
- Production:  mpremote cp file.ext :file.ext (copy to Pico's flash)
"""

import uasyncio as asyncio
import machine
import os
from phew import access_point, dns

# ── Configuration ─────────────────────────────────────────────────────────────
AP_SSID     = "networkPoetics"
AP_PASSWORD = "poetics123"

# Built-in LED — lights up when the WiFi AP is active
led = machine.Pin("LED", machine.Pin.OUT)

# SD card SPI pins — change if you wired differently
SD_SCK  = 2
SD_MOSI = 3
SD_MISO = 4
SD_CS   = 5

# ── SD Card ───────────────────────────────────────────────────────────────────
SD_MOUNTED = False
try:
    import sdcard
    spi = machine.SPI(0, baudrate=20_000_000, polarity=0, phase=0,
                      sck=machine.Pin(SD_SCK),
                      mosi=machine.Pin(SD_MOSI),
                      miso=machine.Pin(SD_MISO))
    sd = sdcard.SDCard(spi, machine.Pin(SD_CS))
    os.mount(os.VfsFat(sd), "/sd")
    SD_MOUNTED = True
    print("SD card mounted at /sd")
except Exception as e:
    print(f"No SD card (continuing without): {e}")

# ── Access Point + DNS ────────────────────────────────────────────────────────
print("Starting access point...")
ap = access_point(AP_SSID, password=AP_PASSWORD)
ip = ap.ifconfig()[0]
led.on()
print(f"AP: {AP_SSID}  IP: {ip}")

dns.run_catchall(ip)
print(f"DNS catchall -> {ip}")

# ── MIME types ────────────────────────────────────────────────────────────────
MIME = {
    ".html": "text/html; charset=utf-8",
    ".css":  "text/css",
    ".js":   "text/javascript",
    ".json": "application/json",
    ".txt":  "text/plain",
    ".ico":  "image/x-icon",
    ".svg":  "image/svg+xml",
    ".jpg":  "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png":  "image/png",
    ".gif":  "image/gif",
    ".webp": "image/webp",
    ".mp4":  "video/mp4",
    ".webm": "video/webm",
    ".mp3":  "audio/mpeg",
    ".wav":  "audio/wav",
    ".pdf":  "application/pdf",
}

CHUNK_SIZE = 8192  # bytes per read — safe for Pico 2W's 520 KB RAM

CAPTIVE_PATHS = frozenset([
    "/generate_204", "/gen_204",
    "/connecttest.txt", "/ncsi.txt",
    "/hotspot-detect.html",
    "/success.txt", "/library/test/success.html",
])

FALLBACK_HTML = b"""<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>networkPoetics</title>
  <style>
    body { font-family: monospace; margin: 0;
           background: linear-gradient(135deg,#1e3c72,#7e22ce);
           color: #fff; min-height: 100vh;
           display: flex; align-items: center; justify-content: center; }
    div  { text-align: center; padding: 2em; }
    h1   { font-size: 2.5em; margin-bottom: 0.5em; }
    p    { opacity: 0.8; }
    code { background: rgba(0,0,0,0.3); padding: 2px 8px; border-radius: 4px; }
  </style>
</head>
<body>
  <div>
    <h1>networkPoetics</h1>
    <p>Upload your index.html to customise this page:</p>
    <p><code>mpremote cp index.html :index.html</code></p>
  </div>
</body>
</html>"""

# ── File helpers ──────────────────────────────────────────────────────────────
def mime_for(path):
    p = path.lower()
    for ext, ct in MIME.items():
        if p.endswith(ext):
            return ct
    return "application/octet-stream"

def find_file(path):
    """Locate a file, return (filepath, mime) or (None, None)."""
    ct = mime_for(path)
    candidates = [f"/remote{path}"]
    if SD_MOUNTED:
        candidates.append(f"/sd{path}")
    candidates.append(path)
    for candidate in candidates:
        try:
            os.stat(candidate)
            return candidate, ct
        except:
            pass
    return None, None

# ── Raw HTTP helpers ──────────────────────────────────────────────────────────
async def send(writer, status, content_type, body):
    if isinstance(body, str):
        body = body.encode()
    hdr = (
        f"HTTP/1.1 {status}\r\n"
        f"Content-Type: {content_type}\r\n"
        f"Content-Length: {len(body)}\r\n"
        "Connection: close\r\n"
        "\r\n"
    ).encode()
    writer.write(hdr)
    writer.write(body)
    await writer.drain()

async def send_file(writer, content_type, filepath, range_header=None):
    """Stream a file in chunks. Supports HTTP Range requests for audio/video."""
    size = os.stat(filepath)[6]

    # Parse Range header (e.g. "bytes=0-" or "bytes=1024-2047")
    start, end = 0, size - 1
    is_range = False
    if range_header and range_header.startswith("bytes="):
        is_range = True
        r = range_header[6:].split("-")
        start = int(r[0]) if r[0] else 0
        end   = int(r[1]) if len(r) > 1 and r[1] else size - 1
        end   = min(end, size - 1)

    length = end - start + 1
    status = "206 Partial Content" if is_range else "200 OK"
    hdr = (
        f"HTTP/1.1 {status}\r\n"
        f"Content-Type: {content_type}\r\n"
        f"Content-Length: {length}\r\n"
        f"Content-Range: bytes {start}-{end}/{size}\r\n"
        "Accept-Ranges: bytes\r\n"
        "Connection: close\r\n"
        "\r\n"
    ).encode()
    writer.write(hdr)
    await writer.drain()

    with open(filepath, "rb") as f:
        if start:
            f.seek(start)
        remaining = length
        n = 0
        while remaining > 0:
            chunk = f.read(min(CHUNK_SIZE, remaining))
            if not chunk:
                break
            writer.write(chunk)
            remaining -= len(chunk)
            n += 1
            if n % 4 == 0:
                await writer.drain()
        await writer.drain()
    print(f"  streamed {filepath} ({start}-{end}/{size})")

async def send_redirect(writer, location):
    hdr = (
        "HTTP/1.1 302 Found\r\n"
        f"Location: {location}\r\n"
        "Content-Length: 0\r\n"
        "Connection: close\r\n"
        "\r\n"
    ).encode()
    writer.write(hdr)
    await writer.drain()

# ── HTTP request handler ──────────────────────────────────────────────────────
async def handle(reader, writer):
    try:
        # Read request line
        line = await asyncio.wait_for(reader.readline(), 5)
        if not line:
            return
        parts = line.decode().split()
        if len(parts) < 2:
            return
        path = parts[1].split("?")[0]   # strip query string

        # Drain remaining headers, capture Range if present
        range_header = None
        while True:
            h = await asyncio.wait_for(reader.readline(), 5)
            if h in (b"\r\n", b"\n", b""):
                break
            hl = h.decode()
            if hl.lower().startswith("range:"):
                range_header = hl.split(":", 1)[1].strip()

        print(f"GET {path}" + (f" [{range_header}]" if range_header else ""))

        # 1. Captive portal OS detection → redirect to portal
        if path in CAPTIVE_PATHS:
            await send_redirect(writer, f"http://{ip}/")
            return

        # 2. Root → serve index
        if path in ("/", ""):
            fp, _ = find_file("/index.html")
            if fp:
                await send_file(writer, "text/html; charset=utf-8", fp)
            else:
                await send(writer, "200 OK", "text/html; charset=utf-8", FALLBACK_HTML)
            return

        # 3. Static files
        fp, ct = find_file(path)
        if fp:
            await send_file(writer, ct, fp, range_header)
            return

        # 4. Anything else → serve index (keeps captive portal visible)
        fp, _ = find_file("/index.html")
        if fp:
            await send_file(writer, "text/html; charset=utf-8", fp)
        else:
            await send(writer, "200 OK", "text/html; charset=utf-8", FALLBACK_HTML)

    except Exception as e:
        print(f"handler error: {e}")
    finally:
        try:
            writer.close()
            await writer.wait_closed()
        except:
            pass

# ── Main loop ─────────────────────────────────────────────────────────────────
async def main():
    srv = await asyncio.start_server(handle, "0.0.0.0", 80, backlog=4)
    print(f"\n{'='*45}")
    print("Captive Portal Ready!")
    print(f"{'='*45}")
    print(f"SSID:     {AP_SSID}")
    print(f"Password: {AP_PASSWORD}")
    print(f"URL:      http://{ip}")
    print(f"{'='*45}\n")
    while True:
        await asyncio.sleep(1)

asyncio.run(main())
