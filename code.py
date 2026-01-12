import wifi
import socketpool
import time
import struct

# Access Point Configuration
AP_SSID = "networkPoetics"
AP_PASSWORD = "poetics123"  # Password required - many devices won't connect to open captive portals

# DNS Server Configuration
DNS_PORT = 53
REDIRECT_IP = "192.168.4.1"  # The Pico's IP address

# HTTP Server Configuration
HTTP_PORT = 80

print("Setting up Access Point...")
# Start AP with password
# The AP will automatically run a DHCP server that tells clients to use this device as DNS
wifi.radio.start_ap(ssid=AP_SSID, password=AP_PASSWORD)
print(f"Access Point started: {AP_SSID}")
print(f"IP Address: {wifi.radio.ipv4_address_ap}")

# Set this device as the DNS server for the access point
# Note: CircuitPython's AP mode should automatically configure DHCP to point DNS to the gateway (this device)
try:
    # Try to configure DNS (this may not be supported in all CircuitPython versions)
    wifi.radio.ipv4_dns_ap = wifi.radio.ipv4_address_ap
    print(f"DNS server set to: {wifi.radio.ipv4_address_ap}")
except AttributeError:
    print("DNS configuration not available, relying on default DHCP settings")

# Create socket pool
pool = socketpool.SocketPool(wifi.radio)

# Load HTML content
try:
    with open("index.html", "r") as f:
        html_content = f.read()
    print("HTML file loaded successfully")
except Exception as e:
    print(f"Error loading HTML file: {e}")
    html_content = "<html><body><h1>Welcome to Pico W2!</h1><p>Error loading index.html</p></body></html>"

# Simple DNS response function
def create_dns_response(query_data, redirect_ip):
    """Create a DNS response that redirects all queries to our IP"""
    try:
        # Extract transaction ID from query
        transaction_id = query_data[0:2]

        # DNS response header
        flags = b'\x81\x80'  # Standard query response
        questions = b'\x00\x01'  # 1 question
        answer_rrs = b'\x00\x01'  # 1 answer
        authority_rrs = b'\x00\x00'
        additional_rrs = b'\x00\x00'

        # Find end of question section
        i = 12
        while i < len(query_data) and query_data[i] != 0:
            i += query_data[i] + 1
        i += 5  # Skip null byte + QTYPE + QCLASS

        question_section = query_data[12:i]

        # Answer section
        answer_name = b'\xc0\x0c'  # Pointer to name in question
        answer_type = b'\x00\x01'  # A record
        answer_class = b'\x00\x01'  # IN
        answer_ttl = b'\x00\x00\x00\x3c'  # 60 seconds TTL
        answer_length = b'\x00\x04'  # 4 bytes

        # Convert IP to bytes
        ip_bytes = bytes([int(x) for x in redirect_ip.split('.')])

        # Build complete response
        response = (transaction_id + flags + questions + answer_rrs +
                   authority_rrs + additional_rrs + question_section +
                   answer_name + answer_type + answer_class + answer_ttl +
                   answer_length + ip_bytes)

        return response
    except:
        return None

# HTTP Server function
def handle_http_request(client_socket):
    """Handle HTTP requests and serve HTML"""
    try:
        print("Receiving HTTP request...")
        request_data = bytearray()
        buffer = bytearray(512)

        # Receive data in chunks using recv_into (CircuitPython API)
        while True:
            try:
                nbytes = client_socket.recv_into(buffer, 512)
                if nbytes == 0:
                    break
                request_data.extend(buffer[:nbytes])
                if b'\r\n\r\n' in request_data:  # End of HTTP headers
                    break
            except OSError:
                break

        request = request_data.decode('utf-8')
        print(f"HTTP Request received ({len(request)} bytes):\n{request[:200]}...")  # Print first 200 chars

        # Check if this is a captive portal detection request
        is_captive_check = False
        if "generate_204" in request or "connecttest" in request or "hotspot-detect" in request:
            is_captive_check = True
            print("Captive portal detection request detected")

        # For captive portal detection, respond with redirect
        if is_captive_check:
            response = "HTTP/1.1 302 Found\r\n"
            response += f"Location: http://{wifi.radio.ipv4_address_ap}/\r\n"
            response += "Content-Length: 0\r\n"
            response += "Connection: close\r\n"
            response += "\r\n"
        else:
            # Build HTTP response - serve HTML for ALL requests (captive portal behavior)
            response = "HTTP/1.1 200 OK\r\n"
            response += "Content-Type: text/html\r\n"
            response += "Connection: close\r\n"
            response += f"Content-Length: {len(html_content)}\r\n"
            response += "\r\n"
            response += html_content

        print(f"Sending response ({len(response)} bytes total)...")

        # Send all data - CircuitPython's send should handle this
        response_bytes = response.encode('utf-8')
        total_sent = 0
        while total_sent < len(response_bytes):
            sent = client_socket.send(response_bytes[total_sent:])
            if sent == 0:
                print("Socket send returned 0, connection may be closed")
                break
            total_sent += sent
        print(f"Successfully sent {total_sent}/{len(response_bytes)} bytes")
    except Exception as e:
        print(f"HTTP error: {e}")
        import traceback
        traceback.print_exception(e)
    finally:
        try:
            client_socket.close()
            print("Client socket closed")
        except:
            pass

# Create DNS socket
dns_socket = None
try:
    dns_socket = pool.socket(pool.AF_INET, pool.SOCK_DGRAM)
    dns_socket.setblocking(False)
    dns_socket.bind(('0.0.0.0', DNS_PORT))
    print(f"DNS server listening on port {DNS_PORT}")
except Exception as e:
    print(f"Warning: Could not create DNS socket: {e}")
    dns_socket = None

# Create HTTP socket
http_socket = pool.socket(pool.AF_INET, pool.SOCK_STREAM)
http_socket.setblocking(False)

# Set socket options to reuse address (prevents EADDRINUSE error)
try:
    http_socket.setsockopt(pool.SOL_SOCKET, pool.SO_REUSEADDR, 1)
except AttributeError:
    # Some CircuitPython versions may not support setsockopt
    pass

http_socket.bind(('0.0.0.0', HTTP_PORT))
http_socket.listen(5)
print(f"HTTP server listening on port {HTTP_PORT}")

print("\nCaptive Portal Ready!")
print(f"Connect to WiFi: {AP_SSID}")
print(f"Password: {AP_PASSWORD}")
print(f"Access the page at: http://{wifi.radio.ipv4_address_ap}")
print(f"HTML content loaded: {len(html_content)} bytes")
print("The webpage should automatically appear.\n")
print("Waiting for connections...")

# Track last DNS client for responses
last_dns_client = None

# Main server loop
while True:
    try:
        # Handle DNS requests if socket is available
        if dns_socket:
            try:
                buffer = bytearray(512)
                nbytes = dns_socket.recv_into(buffer, 512)
                if nbytes and nbytes > 0:
                    query = buffer[:nbytes]
                    response = create_dns_response(query, REDIRECT_IP)
                    if response:
                        # Try multiple strategies to send response
                        sent = False

                        # Strategy 1: Send to last known client
                        if last_dns_client:
                            try:
                                dns_socket.sendto(response, last_dns_client)
                                print(f"DNS response sent to {last_dns_client}")
                                sent = True
                            except:
                                pass

                        # Strategy 2: Try broadcast to subnet
                        if not sent:
                            try:
                                dns_socket.sendto(response, ('192.168.4.255', 53))
                                print(f"DNS query handled ({nbytes} bytes) - broadcast response")
                                sent = True
                            except:
                                pass

                        # Strategy 3: Try global broadcast
                        if not sent:
                            try:
                                dns_socket.sendto(response, ('255.255.255.255', 53))
                                print(f"DNS query handled ({nbytes} bytes) - global broadcast")
                            except:
                                pass
            except OSError:
                pass  # No DNS data available

        # Handle HTTP requests
        try:
            client, addr = http_socket.accept()
            print(f"Connection from {addr}")

            # Update last known client for DNS responses
            last_dns_client = (addr[0], 53)

            client.setblocking(True)
            client.settimeout(5.0)  # 5 second timeout to prevent hanging
            handle_http_request(client)
        except OSError:
            pass  # No HTTP connection available

        time.sleep(0.01)  # Small delay to prevent busy waiting

    except KeyboardInterrupt:
        print("\nShutting down...")
        if dns_socket:
            dns_socket.close()
        http_socket.close()
        break
    except Exception as e:
        print(f"Server error: {e}")
        time.sleep(1)
