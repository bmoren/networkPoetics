"""
Network Poetics Captive Portal — Josie Edition
MicroPython - Raspberry Pi Pico W

INA219 current sensor detects plasma ball touch → enables WiFi AP.
WiFi is OFF at boot; touching the plasma ball activates the network.

── Wiring ────────────────────────────────────────────────────────────────────
  INA219 SDA  → GP6     (I2C1 — avoids conflict with SPI0 SD card on GP2-5)
  INA219 SCL  → GP7
  INA219 VCC  → 3.3V
  INA219 GND  → GND
  INA219 VIN+ → wire taped/wrapped to the outer glass of the plasma ball
  INA219 VIN- → GND    (onboard 0.1Ω shunt sits between VIN- and GND)

  When a hand touches the ball the induced current through the sensing wire
  rises above TOUCH_THRESHOLD_MA and the AP activates.  Remove your hand and
  after AP_TIMEOUT_S of inactivity the AP shuts back down.

── Tuning ────────────────────────────────────────────────────────────────────
  TOUCH_THRESHOLD_MA  (default 0.5 mA)
    The current level that counts as a touch.  The plasma ball produces a
    small baseline current even when idle; this value must sit above that
    noise floor but below what you see when a hand is on the glass.

    How to dial it in:
    1. Open a serial console (mpremote connect / Thonny REPL).
    2. The touch_monitor loop prints the live mA reading on every event.
    3. Note the idle reading (no hand) and the touched reading (hand on ball).
    4. Set TOUCH_THRESHOLD_MA to roughly halfway between the two values.
    5. TOUCH_HYSTERESIS_MA is the dead-band around that threshold — increase
       it if the AP flickers on/off at the boundary (default 0.2 mA).

    If the gap between idle and touched is too small to threshold reliably,
    swap the onboard 0.1 Ω shunt resistor for a larger value (1 Ω–10 Ω) and
    update the INA219(i2c, shunt_ohms=…) call below.  A bigger shunt creates
    a larger voltage drop for the same current, improving resolution.

  AP_TIMEOUT_S  (default 30 s)
    How many seconds the WiFi AP stays on after the last touch event before
    shutting itself back down.  Tune this to taste:
      • Short  (5–10 s)  — AP disappears quickly after release; more private.
      • Medium (30–60 s) — gives visitors time to connect and load the page.
      • Long   (300 s+)  — effectively "stays on for the whole performance".
    Set to a very large number (e.g. 999999) to keep the AP on indefinitely
    once triggered for the first time.
──────────────────────────────────────────────────────────────────────────────
"""

import uasyncio as asyncio
import machine
import network
import os
import struct
import utime
from phew import dns

# ── Configuration ─────────────────────────────────────────────────────────────
AP_SSID     = "networkPoetics"
AP_PASSWORD = "poetics123"

# INA219 I2C bus (I2C1)
INA219_SDA  = 6
INA219_SCL  = 7
INA219_ADDR = 0x40          # default address: A0=GND, A1=GND

# Touch detection
TOUCH_THRESHOLD_MA  = 0.5   # mA  — absolute current above this = touch
TOUCH_HYSTERESIS_MA = 0.2   # mA  — prevents rapid on/off toggling
POLL_INTERVAL_MS    = 100   # ms  — sensor polling rate

# How long (seconds) the AP stays on after the last touch event
AP_TIMEOUT_S = 30

# Debounce: consecutive samples required to confirm touch ON / touch OFF.
# The plasma ball signal is pulsed, so a single sample is not reliable.
# Raise these numbers if the AP still flickers; lower them for faster response.
TOUCH_CONFIRM_SAMPLES  = 3   # samples above threshold  → declare "touched"
RELEASE_CONFIRM_SAMPLES = 8  # samples below threshold  → declare "released"

# SD card SPI pins (unchanged from main.py)
SD_SCK  = 2
SD_MOSI = 3
SD_MISO = 4
SD_CS   = 5

# ── INA219 driver ─────────────────────────────────────────────────────────────
class INA219:
    """Minimal INA219 I2C current/power sensor driver for MicroPython.

    Default calibration targets ±2 A full-scale with a 0.1 Ω shunt.
    Pass shunt_ohms to match whatever shunt resistor you are using.
    """
    _REG_CONFIG  = 0x00
    _REG_SHUNT   = 0x01
    _REG_BUS     = 0x02
    _REG_CALIB   = 0x05
    _REG_CURRENT = 0x04

    def __init__(self, i2c, addr=0x40, shunt_ohms=0.1):
        self._i2c        = i2c
        self._addr       = addr
        self._shunt_ohms = shunt_ohms
        self._calibrate()

    def _write_reg(self, reg, value):
        self._i2c.writeto_mem(self._addr, reg, struct.pack('>H', value))

    def _read_reg(self, reg):
        data = self._i2c.readfrom_mem(self._addr, reg, 2)
        return struct.unpack('>H', data)[0]

    def _calibrate(self):
        # current_lsb = 0.1 mA/bit  →  max current = 3.2767 A
        self._current_lsb = 0.0001   # A/bit
        calib = int(0.04096 / (self._current_lsb * self._shunt_ohms))
        self._write_reg(self._REG_CALIB, calib)
        # Config: 32 V bus, ±320 mV shunt PGA, 12-bit ADC, continuous mode
        self._write_reg(self._REG_CONFIG, 0x399F)

    def current_ma(self):
        """Return signed current in milliamps."""
        raw = self._read_reg(self._REG_CURRENT)
        if raw > 32767:
            raw -= 65536
        return raw * self._current_lsb * 1000.0

    def shunt_voltage_mv(self):
        """Return shunt voltage in millivolts (useful for direct threshold tuning)."""
        raw = self._read_reg(self._REG_SHUNT)
        if raw > 32767:
            raw -= 65536
        return raw * 0.01   # 10 µV/bit → mV

    def bus_voltage_v(self):
        """Return bus voltage in volts."""
        raw = self._read_reg(self._REG_BUS)
        return (raw >> 3) * 0.004   # 4 mV/bit

# ── Hardware init ─────────────────────────────────────────────────────────────
led = machine.Pin("LED", machine.Pin.OUT)
led.off()

# INA219 on I2C1
i2c = machine.I2C(1, sda=machine.Pin(INA219_SDA), scl=machine.Pin(INA219_SCL), freq=400_000)

ina = None
try:
    ina = INA219(i2c, addr=INA219_ADDR)
    print(f"INA219 ready on I2C1 (GP{INA219_SDA}/GP{INA219_SCL})")
    print(f"  bus={ina.bus_voltage_v():.3f} V  shunt={ina.shunt_voltage_mv():.3f} mV  "
          f"current={ina.current_ma():.3f} mA")
except Exception as e:
    print(f"INA219 init failed: {e}")
    print("Touch detection disabled — AP will start immediately as fallback.")

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

# ── WiFi AP (starts inactive) ─────────────────────────────────────────────────
ap_wlan    = network.WLAN(network.AP_IF)
ap_active  = False
dns_started = False
ip          = "192.168.4.1"   # Pico W default AP address

async def _bring_up_ap():
    """Activate the WiFi AP interface and wait until it has a valid IP."""
    global ip
    ap_wlan.active(True)
    if AP_PASSWORD:
        ap_wlan.config(ssid=AP_SSID, password=AP_PASSWORD, security=4)  # WPA2
    else:
        ap_wlan.config(ssid=AP_SSID, security=0)                        # open
    # Poll until the interface assigns itself an IP (avoids NoneType crash)
    for _ in range(30):  # up to 3 seconds
        cfg = ap_wlan.ifconfig()
        if cfg[0] and cfg[0] != "0.0.0.0":
            ip = cfg[0]
            return
        await asyncio.sleep_ms(100)
    ip = "192.168.4.1"  # fallback if ifconfig never settles

def _bring_down_ap():
    """Deactivate the WiFi AP interface."""
    ap_wlan.active(False)

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

CHUNK_SIZE = 8192

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
        line = await asyncio.wait_for(reader.readline(), 5)
        if not line:
            return
        parts = line.decode().split()
        if len(parts) < 2:
            return
        path = parts[1].split("?")[0]

        range_header = None
        while True:
            h = await asyncio.wait_for(reader.readline(), 5)
            if h in (b"\r\n", b"\n", b""):
                break
            hl = h.decode()
            if hl.lower().startswith("range:"):
                range_header = hl.split(":", 1)[1].strip()

        print(f"GET {path}" + (f" [{range_header}]" if range_header else ""))

        if path in CAPTIVE_PATHS:
            await send_redirect(writer, f"http://{ip}/")
            return

        if path in ("/", ""):
            fp, _ = find_file("/index.html")
            if fp:
                await send_file(writer, "text/html; charset=utf-8", fp)
            else:
                await send(writer, "200 OK", "text/html; charset=utf-8", FALLBACK_HTML)
            return

        fp, ct = find_file(path)
        if fp:
            await send_file(writer, ct, fp, range_header)
            return

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

# ── Touch / AP state machine ──────────────────────────────────────────────────
async def touch_monitor():
    # Poll INA219 and toggle the AP based on plasma ball touch.
    global ap_active, dns_started, ip

    touch_state  = False   # True while finger on ball
    last_touch_t = 0       # monotonic ms timestamp of last touch event

    # If INA219 failed at init, just enable AP immediately as a fallback
    if ina is None:
        print("No INA219 — starting AP immediately (fallback mode).")
        await _bring_up_ap()
        ap_active = True
        led.on()
        dns.run_catchall(ip)
        dns_started = True
        print(f"AP: {AP_SSID}  IP: {ip}")
        return  # exit coroutine — AP stays on permanently

    # ── Baseline calibration ──────────────────────────────────────────────────
    # The plasma ball draws significant idle current; we measure a baseline
    # at startup and look for *delta* from that value, not an absolute level.
    BASELINE_SAMPLES = 20
    print(f"Calibrating baseline over {BASELINE_SAMPLES} samples...")
    samples = []
    for _ in range(BASELINE_SAMPLES):
        try:
            samples.append(ina.current_ma())
        except:
            pass
        await asyncio.sleep_ms(POLL_INTERVAL_MS)
    baseline = sum(samples) / len(samples) if samples else 0.0
    print(f"Baseline: {baseline:.3f} mA  |  Touch delta threshold: ±{TOUCH_THRESHOLD_MA} mA")
    print("Waiting for plasma ball touch to activate WiFi...\n")

    touch_count   = 0   # consecutive samples above threshold
    release_count = 0   # consecutive samples below release threshold

    while True:
        # Read current delta from idle baseline
        try:
            delta = abs(ina.current_ma() - baseline)
        except Exception as e:
            print(f"INA219 read error: {e}")
            await asyncio.sleep_ms(POLL_INTERVAL_MS)
            continue

        now = utime.ticks_ms()

        # ── Waiting for touch ─────────────────────────────────────────────────
        if not touch_state:
            if delta >= TOUCH_THRESHOLD_MA:
                touch_count += 1
                if touch_count >= TOUCH_CONFIRM_SAMPLES:
                    touch_state   = True
                    touch_count   = 0
                    release_count = 0
                    last_touch_t  = now
                    print(f"TOUCH detected  (delta={delta:.3f} mA)")
                    if not ap_active:
                        await _bring_up_ap()
                        ap_active = True
                        led.on()
                        if not dns_started:
                            dns.run_catchall(ip)
                            dns_started = True
                        print(f"AP ON  →  SSID: {AP_SSID}  IP: {ip}")
            else:
                touch_count = 0   # reset — must be consecutive

        # ── Touch is active ───────────────────────────────────────────────────
        else:
            if delta >= (TOUCH_THRESHOLD_MA - TOUCH_HYSTERESIS_MA):
                last_touch_t  = now   # still touching — keep AP timeout fresh
                release_count = 0
            else:
                release_count += 1
                if release_count >= RELEASE_CONFIRM_SAMPLES:
                    touch_state   = False
                    release_count = 0
                    print(f"TOUCH released  (delta={delta:.3f} mA)")

        # ── AP timeout after last touch ───────────────────────────────────────
        if ap_active and not touch_state:
            elapsed_s = utime.ticks_diff(now, last_touch_t) / 1000
            if elapsed_s >= AP_TIMEOUT_S:
                _bring_down_ap()
                ap_active = False
                led.off()
                print(f"AP OFF  (no touch for {AP_TIMEOUT_S}s)")

        await asyncio.sleep_ms(POLL_INTERVAL_MS)

# ── Main loop ─────────────────────────────────────────────────────────────────
async def main():
    # HTTP server always listening; only reachable once AP activates
    srv = await asyncio.start_server(handle, "0.0.0.0", 80, backlog=4)
    print(f"\n{'='*45}")
    print("Network Poetics — Josie Edition")
    print(f"{'='*45}")
    print(f"SSID:     {AP_SSID}")
    print(f"Password: {AP_PASSWORD}")
    print(f"Sensor:   INA219 on I2C1  GP{INA219_SDA}/GP{INA219_SCL}")
    print(f"Timeout:  {AP_TIMEOUT_S}s after last touch")
    print(f"{'='*45}\n")

    asyncio.create_task(touch_monitor())

    while True:
        await asyncio.sleep(1)

asyncio.run(main())
