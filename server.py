# server.py
import socket
import threading
from sympy import randprime
import json

# Generate prime numbers once for all clients
q = randprime(100, 200)
g = randprime(2, q)

clients = {}  # Dictionary to store {client_socket: public_key}

def send_primes(client_socket):
    """Send the prime numbers to a new client"""
    prime_data = {
        'q': q,
        'g': g,
        'type': 'primes'
    }
    client_socket.sendall(json.dumps(prime_data).encode())

def broadcast_public_key(sender_socket, public_key):
    """Broadcast a client's public key to all other clients"""
    key_data = {
        'type': 'public_key',
        'public_key': public_key
    }
    for client in clients:
        if client != sender_socket:
            client.sendall(json.dumps(key_data).encode())

def send_existing_keys(new_client):
    """Send existing public keys to a new client"""
    for client, public_key in clients.items():
        if client != new_client and public_key is not None:
            key_data = {
                'type': 'public_key',
                'public_key': public_key
            }
            new_client.sendall(json.dumps(key_data).encode())

def broadcast_message(message, sender):
    """Broadcast encrypted message to all clients except sender"""
    message_data = {
        'type': 'message',
        'content': message
    }
    for client in clients:
        if client != sender:
            client.sendall(json.dumps(message_data).encode())

def handle_client(client_socket):    
    try:
        # Send prime numbers when client connects
        send_primes(client_socket)
        
        # Add client to dictionary with None public key initially
        clients[client_socket] = None
        
        # Send existing public keys to new client
        send_existing_keys(client_socket)
        
        while True:
            try:
                data = client_socket.recv(4096).decode()
                if not data:
                    break
                
                message_data = json.loads(data)
                
                if message_data['type'] == 'public_key':
                    # Store and broadcast the public key
                    clients[client_socket] = message_data['public_key']
                    broadcast_public_key(client_socket, message_data['public_key'])
                    print(f"Clé publique reçue du clint : {message_data['public_key']}")
                
                elif message_data['type'] == 'message':
                    # Broadcast the encrypted message
                    broadcast_message(message_data['content'], client_socket)
                    print(f"Broadcasting message: {message_data['content']}")
                
            except json.JSONDecodeError:
                print("Received invalid JSON data")
                continue
            except Exception as e:
                print(f"Error handling client message: {e}")
                break
                
    finally:
        # Clean up when client disconnects
        if client_socket in clients:
            del clients[client_socket]
        client_socket.close()
        print("Client déconnecté")

def start_server(host, port):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen()
    print(f"Serveur démarré sur {host}:{port}")
    print(f"Nombres premiers générés - q: {q}, g: {g}")
    
    while True:
        client_socket, address = server_socket.accept()
        print(f"Nouvelle connexion depuis {address}")
        threading.Thread(target=handle_client, args=(client_socket,)).start()

if __name__ == "__main__":
    start_server("192.168.1.9", 12345)