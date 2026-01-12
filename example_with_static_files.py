"""
Example: main.py with static file serving
Shows how to serve CSS, JS, and other files alongside HTML
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

# Start DNS catchall
dns.run_catchall(ip)
print(f"DNS server routing all queries to {ip}")

# Helper function to load file with fallback paths
def load_file(filename, content_type="text/html", default_content=""):
    """Load file from /remote/ (mpremote mount) or local filesystem"""
    paths = [f"/remote/{filename}", filename]
    for path in paths:
        try:
            with open(path, "r") as f:
                content = f.read()
            print(f"Loaded {filename} from {path}")
            return content, content_type
        except Exception as e:
            continue
    print(f"File {filename} not found, using default")
    return default_content, content_type

# Load HTML content
html_content, _ = load_file("index.html", default_content="""<!DOCTYPE html>
<html>
<head>
    <title>networkPoetics</title>
    <link rel="stylesheet" href="/style.css">
</head>
<body>
    <h1>Welcome to networkPoetics</h1>
    <script src="/script.js"></script>
</body>
</html>""")

# Captive portal detection routes
@server.route("/generate_204", methods=["GET"])
@server.route("/gen_204", methods=["GET"])
@server.route("/connecttest.txt", methods=["GET"])
@server.route("/hotspot-detect.html", methods=["GET"])
@server.route("/success.txt", methods=["GET"])
def captive_portal_detect(request):
    """Handle OS captive portal detection"""
    print(f"Captive portal detection: {request.path}")
    return "", 302, {"Location": f"http://{ip}/"}

# Main HTML page
@server.route("/", methods=["GET"])
def index(request):
    """Serve main captive portal page"""
    print(f"Serving page to {request.headers.get('Host', 'unknown')}")
    return html_content, 200, {"Content-Type": "text/html; charset=utf-8"}

# Serve CSS file
@server.route("/style.css", methods=["GET"])
def serve_css(request):
    """Serve CSS stylesheet"""
    content, content_type = load_file("style.css", "text/css", default_content="""
body {
    font-family: Arial, sans-serif;
    max-width: 800px;
    margin: 50px auto;
    padding: 20px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
}
h1 {
    text-align: center;
    font-size: 3em;
}
""")
    return content, 200, {"Content-Type": content_type}

# Serve JavaScript file
@server.route("/script.js", methods=["GET"])
def serve_js(request):
    """Serve JavaScript file"""
    content, content_type = load_file("script.js", "application/javascript", default_content="""
console.log('networkPoetics captive portal loaded');

// Example: Show connection time
document.addEventListener('DOMContentLoaded', function() {
    const timeElement = document.createElement('p');
    timeElement.textContent = 'Connected at: ' + new Date().toLocaleTimeString();
    document.body.appendChild(timeElement);
});
""")
    return content, 200, {"Content-Type": content_type}

# API endpoint example
@server.route("/api/status", methods=["GET"])
def api_status(request):
    """API endpoint returning JSON status"""
    import gc

    # Get connected stations (clients)
    try:
        stations = ap.status('stations')
        client_count = len(stations)
    except:
        client_count = 0

    # Build response
    status = {
        "ssid": AP_SSID,
        "ip": ip,
        "clients": client_count,
        "memory_free": gc.mem_free(),
        "uptime": time.time()
    }

    # Manual JSON construction (MicroPython doesn't have json in all builds)
    json_str = "{"
    json_str += f'"ssid": "{status["ssid"]}", '
    json_str += f'"ip": "{status["ip"]}", '
    json_str += f'"clients": {status["clients"]}, '
    json_str += f'"memory_free": {status["memory_free"]}, '
    json_str += f'"uptime": {status["uptime"]}'
    json_str += "}"

    return json_str, 200, {"Content-Type": "application/json"}

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
print(f"API: http://{ip}/api/status")
print("="*50)
print("\nWaiting for connections...")

try:
    server.run()
except KeyboardInterrupt:
    print("\nShutting down...")
