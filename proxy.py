import socket
import threading
import os
import hashlib
import time
import datetime

PROXY_HOST = "0.0.0.0"
PROXY_PORT = 8080

# IP WEBSERVER ASLI
SERVER_HOST = "10.130.64.135"
SERVER_PORT = 8000

BUFFER_SIZE = 4096

CACHE_DIR = "cache"
STATUS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "status")

if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)

cache_lock = threading.Lock()


# CACHE FILE
def get_cache_filename(path):

    filename = hashlib.md5(path.encode()).hexdigest()

    return os.path.join(CACHE_DIR, filename)


# LOAD STATUS PAGE
def load_status_page(status_code):

    status_path = os.path.join(STATUS_DIR, f"{status_code}.html")

    if os.path.exists(status_path):
        with open(status_path, "rb") as f:
            return f.read()

    return None


# BUILD ERROR RESPONSE
def build_error_response(status_code, status_text, fallback_body):

    body = load_status_page(status_code) or fallback_body

    headers = (
        f"HTTP/1.1 {status_code} {status_text}\r\n"
        f"Content-Type: text/html\r\n"
        f"Content-Length: {len(body)}\r\n"
        f"Connection: close\r\n\r\n"
    )

    return headers.encode() + body


# HANDLE CLIENT
def handle_client(client_socket, client_address):

    start_time = time.time()

    try:

        request = client_socket.recv(BUFFER_SIZE)

        if not request:
            client_socket.close()
            return

        request_text = request.decode(errors="ignore")

        print("\n========== REQUEST ==========")
        print(request_text)

        request_line = request_text.split("\r\n")[0]

        try:
            _, path, _ = request_line.split()
        except ValueError:
            client_socket.sendall(build_error_response(
                400, "Bad Request", b"<h1>400 Bad Request</h1>"
            ))
            return

        # Test route untuk demonstrasi 502 (uncomment jika butuh)
        if path == "/force502":
            client_socket.sendall(build_error_response(
                502, "Bad Gateway", b"<h1>502 Bad Gateway</h1>"
            ))
            print(f"[502] {client_address[0]} | {path} | forced")
            return

        cache_file = get_cache_filename(path)

        # =========================
        # CACHE HIT
        # =========================
        if os.path.exists(cache_file):

            with cache_lock:

                with open(cache_file, "rb") as file:
                    cached_response = file.read()

            client_socket.sendall(cached_response)

            duration = (time.time() - start_time) * 1000
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"[HIT] {client_address[0]} | {path} | {timestamp} | {duration:.2f} ms")

        # =========================
        # CACHE MISS
        # =========================
        else:

            server_socket = socket.socket(
                socket.AF_INET,
                socket.SOCK_STREAM
            )

            server_socket.settimeout(2)

            # Connect ke webserver — gagal = 502
            try:
                server_socket.connect((SERVER_HOST, SERVER_PORT))
            except Exception:
                server_socket.close()
                duration = (time.time() - start_time) * 1000
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                print(f"[502] {client_address[0]} | {path} | {timestamp} | {duration:.2f} ms")
                client_socket.sendall(build_error_response(
                    502, "Bad Gateway", b"<h1>502 Bad Gateway</h1>"
                ))
                return

            # Connect berhasil — kirim request, baca response
            try:

                server_socket.sendall(request)

                response = b""

                try:

                    while True:

                        data = server_socket.recv(BUFFER_SIZE)

                        if not data:
                            break

                        response += data

                except socket.timeout:

                    if not response:
                        duration = (time.time() - start_time) * 1000
                        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        print(f"[504] {client_address[0]} | {path} | {timestamp} | {duration:.2f} ms")
                        client_socket.sendall(build_error_response(
                            504, "Gateway Timeout", b"<h1>504 Gateway Timeout</h1>"
                        ))
                        return

            finally:

                server_socket.close()

            # Simpan cache hanya untuk response 200 OK
            if response.startswith(b"HTTP/1.1 200") or response.startswith(b"HTTP/1.0 200"):
                with cache_lock:
                    with open(cache_file, "wb") as file:
                        file.write(response)

            # Kirim ke client/browser
            client_socket.sendall(response)

            duration = (time.time() - start_time) * 1000
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"[MISS] {client_address[0]} | {path} | {timestamp} | {duration:.2f} ms")

    except Exception as e:

        print(f"[ERROR] {e}")

        client_socket.sendall(build_error_response(
            502, "Bad Gateway", b"<h1>502 Bad Gateway</h1>"
        ))

    finally:

        client_socket.close()


# START PROXY
def start_proxy():

    proxy_socket = socket.socket(
        socket.AF_INET,
        socket.SOCK_STREAM
    )

    proxy_socket.setsockopt(
        socket.SOL_SOCKET,
        socket.SO_REUSEADDR,
        1
    )

    proxy_socket.bind(
        (PROXY_HOST, PROXY_PORT)
    )

    proxy_socket.listen(10)

    print(f"[PROXY] Proxy listening on port {PROXY_PORT}, multithreading aktif")

    while True:

        client_socket, client_address = proxy_socket.accept()

        print(f"[NEW CONNECTION] {client_address}")

        thread = threading.Thread(
            target=handle_client,
            args=(client_socket, client_address)
        )

        thread.start()


# MAIN
if __name__ == "__main__":

    start_proxy()
