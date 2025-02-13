import os
import time

def ping_peer(ip):
    """Ping the peer and return True if alive, False otherwise."""
    response = os.system(f"ping -c 1 {ip} > /dev/null 2>&1")
    return response == 0  # 0 means success

def check_liveness():
    global connected_peers

    while True:
        for peer_sock in connected_peers:
            peer_ip = peer_sock.getpeername()[0]

            failed_attempts = 0
            for _ in range(3):  # Try 3 times
                if not ping_peer(peer_ip):
                    failed_attempts += 1
                time.sleep(1)

            if failed_attempts == 3:
                print(f"Peer {peer_ip} is dead. Notifying Seed Nodes.")
                notify_seed_dead_node(peer_ip)

        time.sleep(13)  # Wait before the next liveness check

def notify_seed_dead_node(dead_ip):
    try:
        seed_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        seed_sock.connect(("127.0.0.1", 5000))  # Connect to the Seed Node
        seed_sock.send(f"DEAD_NODE:{dead_ip}".encode())  # Notify seed
        seed_sock.close()
    except:
        print("Failed to notify Seed Node.")
