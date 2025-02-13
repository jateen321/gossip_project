import socket
import threading
import time
import random
import hashlib
import os

connected_peers = []
message_list = set()

def connect_to_seed(seed_ip, seed_port):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((seed_ip, seed_port))
        sock.send(f"REGISTER:{socket.gethostbyname(socket.gethostname())}:{random.randint(10000, 60000)}".encode())
        response = sock.recv(1024).decode()
        if response == "REGISTERED":
            print("Registered with Seed Node.")
        return sock
    except Exception as e:
        print(f"Failed to connect to seed: {e}")

def request_peer_list(sock):
    try:
        sock.send("REQUEST_PEERS".encode())
        peers = sock.recv(1024).decode().split("\n")
        return [tuple(peer.split(":")) for peer in peers if peer]
    except:
        return []

def connect_to_peers(peer_list):
    global connected_peers
    for ip, port in peer_list:
        try:
            peer_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            peer_sock.connect((ip, int(port)))
            connected_peers.append(peer_sock)
        except:
            continue

def generate_message():
    return f"{time.time()}:{socket.gethostbyname(socket.gethostname())}:{random.randint(1,100)}"

def gossip():
    while True:
        message = generate_message()
        msg_hash = hashlib.sha256(message.encode()).hexdigest()

        if msg_hash not in message_list:
            message_list.add(msg_hash)
            for peer in connected_peers:
                try:
                    peer.send(message.encode())
                except:
                    continue
        time.sleep(5)

def listen_for_messages(peer_sock):
    try:
        while True:
            msg = peer_sock.recv(1024).decode()
            if msg:
                msg_hash = hashlib.sha256(msg.encode()).hexdigest()
                if msg_hash not in message_list:
                    print(f"Received: {msg}")
                    message_list.add(msg_hash)
    except:
        peer_sock.close()

def start_peer():
    seed_sock = connect_to_seed("127.0.0.1", 5000)  # Connect
        if not seed_sock:
        print("Could not connect to Seed Node. Exiting.")
        return

    # Get list of peers from Seed Node
    peer_list = request_peer_list(seed_sock)
    if not peer_list:
        print("No peers found. Exiting.")
        return

    # Connect to a subset of peers (ensure power-law distribution)
    selected_peers = random.sample(peer_list, min(len(peer_list), 3))  # Choose at least 3 peers
    connect_to_peers(selected_peers)

    # Start Gossip Protocol
    gossip_thread = threading.Thread(target=gossip)
    gossip_thread.start()

    # Start Listening for Messages
    for peer in connected_peers:
        listener_thread = threading.Thread(target=listen_for_messages, args=(peer,))
        listener_thread.start()

    # Start Liveness Check
    liveness_thread = threading.Thread(target=check_liveness)
    liveness_thread.start()

