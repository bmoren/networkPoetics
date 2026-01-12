"""
Network Poetics Captive Portal
MicroPython implementation for Raspberry Pi Pico W
Using Pimoroni Phew library for improved DNS and HTTP handling
"""

import network
from phew import server, access_point, dns
import time

# Configuration
AP_SSID = "networkPoetics"
AP_PASSWORD = "poetics123"

# Setup access point
print("Setting up Access Point...")
ap = access_point(AP_SSID, password=AP_PASSWORD)
ip = ap.ifconfig()[0]
print(f"Access Point: {AP_SSID}")
print(f"IP Address: {ip}")

# Start DNS catchall (redirects all queries to this device)
dns.run_catchall(ip)
print(f"DNS server routing all queries to {ip}")

# Load HTML content
# For development: use /remote/index.html (from mpremote mount)
# For production: use index.html (from Pico's flash)
html_paths = ["/remote/index.html", "index.html"]
html_content = None

for path in html_paths:
    try:
        with open(path, "r") as f:
            html_content = f.read()
        print(f"HTML loaded from {path}: {len(html_content)} bytes")
        break
    except Exception as e:
        continue

if html_content is None:
    print("No HTML file found, using fallback")
    html_content = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>networkPoetics</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 600px;
            margin: 50px auto;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            text-align: center;
        }
        h1 {
            font-size: 2.5em;
            margin-bottom: 0.5em;
        }
        p {
            font-size: 1.2em;
            line-height: 1.6;
        }
        .info {
            background: rgba(255, 255, 255, 0.1);
            padding: 20px;
            border-radius: 10px;
            margin-top: 20px;
        }
    </style>
</head>
<body>
    <h1>Welcome to networkPoetics</h1>
    <p>A captive portal experiment exploring network spaces and poetic interactions.</p>
    <div class="info">
        <p><strong>Connected to:</strong> networkPoetics</p>
        <p><strong>Status:</strong> Active</p>
    </div>
</body>
</html>"""

# Captive portal detection routes (iOS, Android, Windows)
@server.route("/generate_204", methods=["GET"])
@server.route("/gen_204", methods=["GET"])
@server.route("/connecttest.txt", methods=["GET"])
@server.route("/hotspot-detect.html", methods=["GET"])
@server.route("/success.txt", methods=["GET"])
def captive_portal_detect(request):
    """Handle OS captive portal detection"""
    print(f"Captive portal detection: {request.path}")
    # Return 302 redirect to trigger portal popup
    return "", 302, {"Location": f"http://{ip}/"}

# Root route - serve main page
@server.route("/", methods=["GET"])
def index(request):
    """Serve captive portal page"""
    print(f"Serving page to {request.headers.get('Host', 'unknown')}")
    return html_content, 200, {"Content-Type": "text/html; charset=utf-8"}

# Catch all other requests
@server.catchall()
def catch_all(request):
    """Serve HTML for any unmatched route"""
    print(f"Catchall: {request.method} {request.path}")
    return html_content, 200, {"Content-Type": "text/html; charset=utf-8"}

# Start server
print("\n" + "="*50)
print("Captive Portal Ready!")
print("="*50)
print(f"SSID: {AP_SSID}")
print(f"Password: {AP_PASSWORD}")
print(f"URL: http://{ip}")
print("="*50)
print("\nWaiting for connections...")

try:
    server.run()
except KeyboardInterrupt:
    print("\nShutting down...")
