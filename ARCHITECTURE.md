# Architecture Overview

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Raspberry Pi Pico W                       │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │                    MicroPython                          │ │
│  │                                                          │ │
│  │  ┌────────────────────────────────────────────────────┐ │ │
│  │  │                  main.py                            │ │ │
│  │  │                                                      │ │ │
│  │  │  ┌──────────────┐  ┌──────────────┐  ┌───────────┐│ │ │
│  │  │  │   Access     │  │     DNS      │  │   HTTP    ││ │ │
│  │  │  │    Point     │  │   Catchall   │  │  Server   ││ │ │
│  │  │  │              │  │              │  │           ││ │ │
│  │  │  │  Phew Lib    │  │  Phew Lib    │  │ Phew Lib  ││ │ │
│  │  │  └──────────────┘  └──────────────┘  └───────────┘│ │ │
│  │  │         │                  │                │       │ │ │
│  │  │         │                  │                │       │ │ │
│  │  │    ┌────▼──────────────────▼────────────────▼────┐ │ │ │
│  │  │    │         uasyncio Event Loop                 │ │ │ │
│  │  │    └─────────────────────────────────────────────┘ │ │ │
│  │  └────────────────────────────────────────────────────┘ │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │                   Filesystem                            │ │
│  │                                                          │ │
│  │  /main.py         - Main application                    │ │
│  │  /index.html      - Portal page (optional)              │ │
│  │  /lib/phew/       - Phew library                        │ │
│  │  /remote/         - mpremote mount (dev only)           │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ WiFi Access Point
                            │ SSID: networkPoetics
                            │ IP: 192.168.4.1
                            │
         ┌──────────────────┼──────────────────┐
         │                  │                  │
    ┌────▼────┐        ┌────▼────┐       ┌────▼────┐
    │  Phone  │        │ Laptop  │       │ Tablet  │
    │  (iOS)  │        │(Windows)│       │(Android)│
    └─────────┘        └─────────┘       └─────────┘
```

## Network Flow

### 1. WiFi Connection

```
User Device
    │
    │ 1. Scan for WiFi networks
    │
    ▼
Sees "networkPoetics"
    │
    │ 2. Connect with password "poetics123"
    │
    ▼
Pico W Access Point
    │
    │ 3. DHCP assigns IP (192.168.4.x)
    │ 4. Sets DNS server to 192.168.4.1 (itself)
    │
    ▼
Connected!
```

### 2. DNS Resolution (The Magic)

```
User Device tries to access google.com
    │
    │ DNS Query: "What's the IP of google.com?"
    │
    ▼
Pico W DNS Server (port 53)
    │
    │ Phew's dns.run_catchall()
    │ Intercepts query
    │
    ▼
Response: "google.com is at 192.168.4.1"
    │
    │ (Lies! But that's the point)
    │
    ▼
User Device: "Got it, connecting to 192.168.4.1"
```

### 3. Captive Portal Detection

```
OS-Specific Detection Request:
    │
    ├─ iOS:      GET /hotspot-detect.html
    ├─ Android:  GET /generate_204
    └─ Windows:  GET /connecttest.txt
    │
    ▼
Pico W HTTP Server (port 80)
    │
    │ Matches route pattern
    │
    ▼
Returns: HTTP 302 Redirect → http://192.168.4.1/
    │
    ▼
OS: "Aha! Captive portal detected!"
    │
    ▼
Opens portal popup automatically
```

### 4. Portal Display

```
User's Browser
    │
    │ GET http://192.168.4.1/
    │
    ▼
Phew HTTP Server
    │
    │ @server.route("/")
    │
    ▼
Loads index.html
    │
    ├─ Checks /remote/index.html (mpremote mount)
    ├─ Falls back to index.html (flash storage)
    └─ Falls back to embedded HTML (last resort)
    │
    ▼
Returns HTML + CSS
    │
    ▼
User sees beautiful portal page!
```

## Code Flow

### Initialization Sequence

```
1. main.py starts
   └─ import network, phew modules
      │
2. Setup Access Point
   └─ access_point(ssid, password)
      ├─ Creates WiFi AP
      ├─ Starts DHCP server
      └─ Returns IP (192.168.4.1)
      │
3. Start DNS Server
   └─ dns.run_catchall(ip)
      ├─ Creates UDP socket on port 53
      ├─ Starts async task
      └─ Redirects all DNS to ip
      │
4. Load HTML Content
   └─ Try /remote/index.html
      └─ Try index.html
         └─ Use fallback HTML
      │
5. Register Routes
   ├─ @server.route("/generate_204")  # iOS/Android
   ├─ @server.route("/connecttest.txt") # Windows
   ├─ @server.route("/")                # Main page
   └─ @server.catchall()                # Everything else
      │
6. Start Server
   └─ server.run()
      └─ uasyncio.run(main())
         ├─ HTTP socket on port 80
         └─ Async event loop forever
```

### Request Handling Flow

```
Incoming Request
    │
    ▼
Phew Router
    │
    ├─ Match exact route?
    │  └─ Yes → Call handler
    │
    ├─ Match pattern route?
    │  └─ Yes → Call handler
    │
    └─ No match?
       └─ Call @catchall handler
    │
    ▼
Handler Function
    │
    ├─ Return (content, status_code, headers)
    │
    ▼
Phew Response Builder
    │
    ├─ Build HTTP response
    ├─ Add headers
    ├─ Add content
    │
    ▼
Send to Client
```

## Async Event Loop

```
┌─────────────────────────────────────────┐
│         uasyncio Event Loop              │
│                                          │
│  ┌────────────┐  ┌────────────┐  ┌────┐│
│  │   Task 1   │  │   Task 2   │  │... ││
│  │            │  │            │  │    ││
│  │    DNS     │  │   HTTP     │  │    ││
│  │  Handler   │  │  Handler   │  │    ││
│  │            │  │            │  │    ││
│  │  async def │  │  async def │  │    ││
│  │  dns_srv() │  │  http_srv()│  │    ││
│  └────────────┘  └────────────┘  └────┘│
│         │              │                │
│         └──────┬───────┘                │
│                │                        │
│         ┌──────▼─────────┐             │
│         │   I/O Queue    │             │
│         │                │             │
│         │  socket.recv() │             │
│         │  socket.send() │             │
│         └────────────────┘             │
│                                         │
└─────────────────────────────────────────┘

Benefits:
- Non-blocking I/O
- Multiple concurrent connections
- Low CPU usage
- Fast response times
```

## Development vs Production

### Development Workflow (mpremote mount)

```
┌──────────────────┐
│   Your PC        │
│                  │
│  /networkPoetics/│
│  ├─ index.html   │ ◄────┐
│  ├─ style.css    │      │
│  └─ script.js    │      │
└──────────────────┘      │
         │                │
         │ USB            │
         │                │
┌────────▼─────────┐      │
│   Pico W         │      │
│                  │      │
│  /remote/        │      │
│  ├─ index.html ──┼──────┘ (symlink-like)
│  ├─ style.css ───┼──────┐
│  └─ script.js ───┼──────┘
│                  │
│  main.py reads   │
│  from /remote/   │
└──────────────────┘

Edit files on PC → Changes live instantly
```

### Production Deployment (copied files)

```
┌──────────────────┐
│   Your PC        │
│                  │
│  mpremote cp     │
│  file.html       │
│  :file.html      │
└──────────────────┘
         │
         │ USB
         │
┌────────▼─────────┐
│   Pico W         │
│                  │
│  /file.html      │ ◄─── Stored in flash
│  /main.py        │
│  /lib/phew/      │
│                  │
│  Runs standalone │
│  No PC needed    │
└──────────────────┘
```

## DNS Packet Flow (Technical)

### CircuitPython Problem

```
Client                  Pico W
  │                       │
  │ DNS Query (UDP)       │
  │──────────────────────>│
  │                       │
  │                       ├─ recv_into(buffer)
  │                       │  Returns: nbytes
  │                       │  Problem: No client address!
  │                       │
  │                       ├─ Strategy 1: Guess from HTTP
  │<──────────────────────┤  sendto(last_http_client)
  │     Miss ~30%         │
  │                       │
  │<──────────────────────┤  Strategy 2: Subnet broadcast
  │     Miss ~20%         │  sendto(192.168.4.255)
  │                       │
  │<══════════════════════┤  Strategy 3: Global broadcast
  │     Success ~70%      │  sendto(255.255.255.255)
```

### MicroPython Solution

```
Client                  Pico W
  │                       │
  │ DNS Query (UDP)       │
  │──────────────────────>│
  │                       │
  │                       ├─ recvfrom(512)
  │                       │  Returns: (data, client_addr)
  │                       │  Success: Has address!
  │                       │
  │                       ├─ Build response
  │                       │  All domains → 192.168.4.1
  │                       │
  │<══════════════════════┤  sendto(response, client_addr)
  │     Success ~99%      │  Direct response!
```

## Memory Layout

```
Pico W RAM (264KB total)
┌───────────────────────────────┐
│ MicroPython Runtime   ~150KB  │
├───────────────────────────────┤
│ Phew Library          ~30KB   │
├───────────────────────────────┤
│ Application Code      ~10KB   │
├───────────────────────────────┤
│ HTML Content          ~4KB    │
├───────────────────────────────┤
│ Network Buffers       ~20KB   │
├───────────────────────────────┤
│ Free Heap             ~50KB   │
└───────────────────────────────┘
```

## Performance Metrics

### DNS Query Processing

```
Request → Process → Response
   │         │          │
   1ms      <1ms       1ms
   └─────────┴──────────┘
   Total: ~2-3ms per query
```

### HTTP Request Processing

```
Connect → Parse → Load HTML → Send → Close
   │        │         │         │       │
  2ms      1ms       5ms       10ms    1ms
  └────────┴─────────┴─────────┴───────┘
  Total: ~20ms per request
```

### Concurrent Operations

```
Time →
────────────────────────────────────────
DNS Query 1  ████
             DNS Query 2  ████
                          HTTP Request ██████████
                               DNS Query 3  ████
                                    HTTP Request ██████████

All handled concurrently via async/await
No blocking, no polling delays
```

## Security Considerations

### What This Does

✅ Creates isolated WiFi network
✅ Captures DNS queries (expected for captive portal)
✅ Serves web content to connected devices
✅ Runs locally on Pico W

### What This Doesn't Do

❌ No internet passthrough (not a gateway)
❌ No data logging or storage
❌ No external network access
❌ No user tracking

### Use Cases

✅ Art installations
✅ Network experiments
✅ Educational demos
✅ Offline web experiences
✅ Event portals

❌ Not for: Malicious captive portals, data theft, network attacks

## Comparison: Old vs New Architecture

### CircuitPython (Synchronous)

```
while True:
    check_dns()     # 10ms
    sleep(0.01)     # 10ms
    check_http()    # 10ms
    sleep(0.01)     # 10ms
    # Cycle: 40ms minimum
    # CPU: Always busy polling
```

### MicroPython (Asynchronous)

```
async def dns_handler():
    while True:
        await socket.recv()  # Sleeps until data
        process()
        send()

async def http_handler():
    while True:
        await socket.accept()  # Sleeps until connection
        process()
        send()

# Both run concurrently
# CPU: Sleeps when idle
```

## Key Takeaways

1. **DNS is the key** - Redirecting DNS queries makes captive portal work
2. **Async is efficient** - Event-driven architecture uses less CPU
3. **Phew simplifies** - Library handles complexity
4. **mpremote is powerful** - Live file serving for development
5. **Pico W is capable** - Handles multiple clients reliably

---

For implementation details, see [main.py](main.py)
For usage instructions, see [README.md](README.md)
For quick commands, see [QUICK_REFERENCE.md](QUICK_REFERENCE.md)
