import socket
import threading
import random

# Global Peer List: {peer_ip: [port, degree]}
peer_list = {}  # Dictionary to track peer connections

def handle_peer(client_socket):
    global peer_list
    try:
        while True:
            data = client_socket.recv(1024).decode()
            if not data:
                break

            # Peer Registration: "REGISTER:<IP>:<PORT>"
            if data.startswith("REGISTER:"):
                _, peer_ip, peer_port = data.split(":")
                peer_list[peer_ip] = [peer_port, 1]  # Initialize with degree 1
                print(f"Peer registered: {peer_ip}:{peer_port}")
                client_socket.send("REGISTERED".encode())

            # Peer Requests Peer List
            elif data == "REQUEST_PEERS":
                selected_peers = select_power_law_peers()
                peer_data = "\n".join([f"{ip}:{info[0]}" for ip, info in selected_peers])
                client_socket.send(peer_data.encode())

            # Dead Node Notification: "DEAD_NODE:<IP>"
            elif data.startswith("DEAD_NODE:"):
                _, dead_peer = data.split(":")
                if dead_peer in peer_list:
                    del peer_list[dead_peer]
                    print(f"Removed dead node: {dead_peer}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        client_socket.close()

def select_power_law_peers():
    """ Select peers using weighted probability based on degree (power-law). """
    if not peer_list:
        return []

    peers = list(peer_list.items())  # Convert dictionary to list of tuples (ip, [port, degree])

    # Assign selection weights based on degree
    weights = [info[1] for _, info in peers]  # Use the degree as weight
    selected_peers = random.choices(peers, weights=weights, k=min(len(peers), 3))  # Select 3 peers

    # Increase degree count for selected peers
    for peer in selected_peers:
        peer_list[peer[0]][1] += 1  # Increment degree count

    return selected_peers  # Return list of (IP, [port, degree])

def start_seed_node(ip, port):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((ip, port))
    server.listen(5)
    print(f"Seed Node listening on {ip}:{port}")

    while True:
        client_socket, _ = server.accept()
        thread = threading.Thread(target=handle_peer, args=(client_socket,))
        thread.start()

if __name__ == "__main__":
    start_seed_node("127.0.0.1", 5000)
