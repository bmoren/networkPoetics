"""
Network Poetics Captive Portal
MicroPython - Raspberry Pi Pico W

Uses Phew for DNS catchall, raw asyncio for HTTP (full control over responses).

File Management:
- Development: mpremote mount . (files served live from your computer)
- Production:  mpremote cp file.ext :file.ext (copy to Pico's flash)
"""

import uasyncio as asyncio
from phew import access_point, dns

# ── Configuration ─────────────────────────────────────────────────────────────
AP_SSID     = "networkPoetics"
AP_PASSWORD = "poetics123"

# ── Access Point + DNS ────────────────────────────────────────────────────────
print("Starting access point...")
ap = access_point(AP_SSID, password=AP_PASSWORD)
ip = ap.ifconfig()[0]
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

BINARY_PREFIXES = ("image/", "video/", "audio/", "application/pdf")

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

def read_file(path):
    """Return (bytes, mime) for path, trying /remote first. None on failure."""
    ct   = mime_for(path)
    mode = "rb" if ct.split(";")[0].startswith(BINARY_PREFIXES) else "r"
    for candidate in (f"/remote{path}", path):
        try:
            with open(candidate, mode) as f:
                data = f.read()
            if isinstance(data, str):
                data = data.encode()
            print(f"  served {candidate} ({len(data)}b)")
            return data, ct
        except:
            pass
    return None, None

def index_bytes():
    data, _ = read_file("/index.html")
    return data if data else FALLBACK_HTML

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

        # Drain remaining headers
        while True:
            h = await asyncio.wait_for(reader.readline(), 5)
            if h in (b"\r\n", b"\n", b""):
                break

        print(f"GET {path}")

        # 1. Captive portal OS detection → redirect to portal
        if path in CAPTIVE_PATHS:
            await send_redirect(writer, f"http://{ip}/")
            return

        # 2. Root → serve index
        if path in ("/", ""):
            await send(writer, "200 OK", "text/html; charset=utf-8", index_bytes())
            return

        # 3. Static files
        data, ct = read_file(path)
        if data:
            await send(writer, "200 OK", ct, data)
            return

        # 4. Anything else → serve index (keeps captive portal visible)
        await send(writer, "200 OK", "text/html; charset=utf-8", index_bytes())

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
