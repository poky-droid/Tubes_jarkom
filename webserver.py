import socket
import threading
import os
from datetime import datetime

HOST = "0.0.0.0"
TCP_PORT = 8000
UDP_PORT = 9000
BUFFER_SIZE = 4096


# HTTP RESPONSE
def build_response(status_code, body):
    status_text = {
        200: "OK",
        404: "Not Found",
        500: "Internal Server Error"
    }

    response = (
        f"HTTP/1.1 {status_code} {status_text[status_code]}\r\n"
        f"Content-Type: text/html; charset=utf-8\r\n"
        f"Content-Length: {len(body.encode())}\r\n"
        f"\r\n"
        f"{body}"
    )

    return response.encode()


# HANDLE TCP CLIENT
def handle_http_client(client_socket, client_address):
    try:
        request = client_socket.recv(BUFFER_SIZE).decode()

        if not request:
            client_socket.close()
            return

        request_line = request.split("\r\n")[0]
        method, path, version = request_line.split()

        print(f"[HTTP] {client_address} -> {path}")

        if method != "GET":
            response = build_response(500, "<h1>500 Internal Server Error</h1>")
            client_socket.sendall(response)
            client_socket.close()
            return

        if path == "/":
            path = "/index.html"

        filepath = "." + path

        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as file:
                body = file.read()

            response = build_response(200, body)

        else:
            response = build_response(404, "<h1>404 Not Found</h1>")

        client_socket.sendall(response)

    except Exception as e:
        print(f"[ERROR] {e}")

        response = build_response(500, "<h1>500 Internal Server Error</h1>")
        client_socket.sendall(response)

    finally:
        client_socket.close()


# TCP SERVER
def start_tcp_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    server_socket.bind((HOST, TCP_PORT))
    server_socket.listen(5)

    print(f"[TCP] Web Server running on port {TCP_PORT}")

    while True:
        client_socket, client_address = server_socket.accept()

        thread = threading.Thread(
            target=handle_http_client,
            args=(client_socket, client_address)
        )

        thread.start()


# UDP ECHO SERVER
def start_udp_server():
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    udp_socket.bind((HOST, UDP_PORT))

    print(f"[UDP] Echo Server running on port {UDP_PORT}")

    while True:
        data, addr = udp_socket.recvfrom(BUFFER_SIZE)

        print(f"[UDP] Packet from {addr}")

        udp_socket.sendto(data, addr)


# MAIN
if __name__ == "__main__":

    tcp_thread = threading.Thread(target=start_tcp_server)
    udp_thread = threading.Thread(target=start_udp_server)

    tcp_thread.start()
    udp_thread.start()