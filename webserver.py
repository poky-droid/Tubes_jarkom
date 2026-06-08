import socket
import threading
import os
import datetime

HOST = "0.0.0.0"
TCP_PORT = 8000
UDP_PORT = 9000
BUFFER_SIZE = 4096

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


# MIME TYPE
def get_content_type(filepath):

    if filepath.endswith(".html"):
        return "text/html; charset=utf-8"

    elif filepath.endswith(".css"):
        return "text/css"

    elif filepath.endswith(".js"):
        return "application/javascript"

    elif filepath.endswith(".png"):
        return "image/png"

    elif filepath.endswith(".jpg") or filepath.endswith(".jpeg"):
        return "image/jpeg"

    elif filepath.endswith(".ico"):
        return "image/x-icon"

    else:
        return "application/octet-stream"


# LOAD STATUS PAGE
def load_status_page(status_code):
    """
    Load custom status page dari folder status jika ada.
    Returns: (body, content_type) atau (None, None) jika tidak ada
    """
    status_filename = f"{status_code}.html"
    status_path = os.path.join(BASE_DIR, "status", status_filename)

    if os.path.exists(status_path):
        try:
            with open(status_path, "rb") as f:
                body = f.read()
            content_type = get_content_type(status_path)
            return body, content_type
        except Exception as e:
            print(f"[WARNING] Failed to load status page {status_code}: {e}")
            return None, None

    return None, None


# BUILD RESPONSE
def build_response(status_code, body, content_type):

    status_text = {
        200: "OK",
        404: "Not Found",
        500: "Internal Server Error",
        502: "Bad Gateway",
        504: "Gateway Timeout"
    }

    headers = (
        f"HTTP/1.1 {status_code} {status_text[status_code]}\r\n"
        f"Content-Type: {content_type}\r\n"
        f"Content-Length: {len(body)}\r\n"
        f"Connection: close\r\n"
        f"\r\n"
    )

    return headers.encode() + body


# HANDLE CLIENT
def handle_http_client(client_socket, client_address):

    try:

        request = client_socket.recv(BUFFER_SIZE).decode(errors="ignore")

        if not request:
            client_socket.close()
            return

        request_line = request.split("\r\n")[0]

        print(f"[REQUEST] {request_line}")

        method, path, version = request_line.split()

        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[HTTP] {client_address[0]} | {path} | {timestamp}")

        # Hanya support GET
        if method != "GET":

            # Gunakan custom 500 page jika ada
            body, content_type = load_status_page(500)

            if body is None:
                body = b"<h1>500 Internal Server Error</h1>"
                content_type = "text/html"

            response = build_response(
                500,
                body,
                content_type
            )

            client_socket.sendall(response)
            client_socket.close()
            return

        # Root
        if path == "/":
            path = "/index.html"

        filepath = os.path.join(
            BASE_DIR,
            path.lstrip("/")
        )

        print(f"[FILEPATH] {filepath}")

        # FILE ADA
        if os.path.exists(filepath):

            with open(filepath, "rb") as file:
                body = file.read()

            content_type = get_content_type(filepath)

            response = build_response(
                200,
                body,
                content_type
            )

            print(f"[200] {client_address[0]} | {path} | {timestamp}")

        # FILE TIDAK ADA
        else:

            # Gunakan custom 404 page jika ada
            body, content_type = load_status_page(404)

            if body is None:
                body = b"<h1>404 Not Found</h1>"
                content_type = "text/html"

            response = build_response(
                404,
                body,
                content_type
            )

            print(f"[404] {client_address[0]} | {path} | {timestamp}")

        client_socket.sendall(response)

    except Exception as e:

        print(f"[ERROR] {e}")

        # Gunakan custom 500 page jika ada
        body, content_type = load_status_page(500)

        if body is None:
            body = b"<h1>500 Internal Server Error</h1>"
            content_type = "text/html"

        response = build_response(
            500,
            body,
            content_type
        )

        client_socket.sendall(response)

    finally:

        client_socket.close()


# TCP SERVER
def start_tcp_server():

    server_socket = socket.socket(
        socket.AF_INET,
        socket.SOCK_STREAM
    )

    server_socket.setsockopt(
        socket.SOL_SOCKET,
        socket.SO_REUSEADDR,
        1
    )

    server_socket.bind((HOST, TCP_PORT))

    server_socket.listen(5)

    print(f"[TCP] Web Server running on port {TCP_PORT}")

    while True:

        client_socket, client_address = server_socket.accept()

        print(f"[NEW CONNECTION] {client_address}")

        thread = threading.Thread(
            target=handle_http_client,
            args=(client_socket, client_address)
        )

        thread.start()


# UDP SERVER
def start_udp_server():

    udp_socket = socket.socket(
        socket.AF_INET,
        socket.SOCK_DGRAM
    )

    udp_socket.bind((HOST, UDP_PORT))

    print(f"[UDP] Echo Server running on port {UDP_PORT}")

    while True:

        data, addr = udp_socket.recvfrom(BUFFER_SIZE)

        print(f"[UDP] Packet from {addr}")

        udp_socket.sendto(data, addr)


# MAIN
if __name__ == "__main__":

    tcp_thread = threading.Thread(
        target=start_tcp_server
    )

    udp_thread = threading.Thread(
        target=start_udp_server
    )

    tcp_thread.start()
    udp_thread.start()