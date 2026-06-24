import socket
import time
import argparse
import statistics

PROXY_HOST = "10.130.64.121"
PROXY_PORT = 8080

SERVER_HOST = "10.130.64.135"
UDP_PORT = 9000

BUFFER_SIZE = 4096


# TCP MODE
def tcp_mode():

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    client_socket.connect((PROXY_HOST, PROXY_PORT))

    request = (
        "GET /index.html HTTP/1.1\r\n"
        "Host: localhost\r\n"
        "\r\n"
    )

    client_socket.sendall(request.encode())

    response = b""

    while True:

        data = client_socket.recv(BUFFER_SIZE)

        if not data:
            break

        response += data

    client_socket.close()

    print(response.decode(errors="ignore"))


# UDP MODE
def udp_mode():

    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    udp_socket.settimeout(1)

    rtts = []
    success = 0
    total_bytes = 0

    total_packets = 10

    start_test = time.time()

    for seq in range(total_packets):

        send_time = time.time()

        message = f"Ping {seq} {send_time}"

        try:

            udp_socket.sendto(
                message.encode(),
                (SERVER_HOST, UDP_PORT)
            )

            data, addr = udp_socket.recvfrom(BUFFER_SIZE)

            recv_time = time.time()

            rtt = (recv_time - send_time) * 1000

            rtts.append(rtt)

            success += 1
            total_bytes += len(data)

            print(f"Reply from {addr} RTT = {rtt:.2f} ms")

        except socket.timeout:

            print("Request timed out")

        time.sleep(1)

    end_test = time.time()

    udp_socket.close()

    # STATISTICS
    if rtts:

        min_rtt = min(rtts)
        max_rtt = max(rtts)
        avg_rtt = sum(rtts) / len(rtts)

        if len(rtts) > 1:
            diffs = [abs(rtts[i] - rtts[i - 1]) for i in range(1, len(rtts))]
            jitter = statistics.stdev(diffs) if len(diffs) > 1 else 0
        else:
            jitter = 0

    else:

        min_rtt = max_rtt = avg_rtt = jitter = 0

    packet_loss = ((total_packets - success) / total_packets) * 100

    duration = end_test - start_test

    throughput = (total_bytes * 8) / duration / 1000

    print("\n===== QoS Statistics =====")
    print(f"Min RTT     : {min_rtt:.2f} ms")
    print(f"Avg RTT     : {avg_rtt:.2f} ms")
    print(f"Max RTT     : {max_rtt:.2f} ms")
    print(f"Packet Loss : {packet_loss:.2f}%")
    print(f"Jitter      : {jitter:.2f} ms")
    print(f"Throughput  : {throughput:.2f} kbps")


# MAIN
if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--mode",
        choices=["tcp", "udp"],
        required=True
    )

    args = parser.parse_args()

    if args.mode == "tcp":
        tcp_mode()

    elif args.mode == "udp":
        udp_mode()