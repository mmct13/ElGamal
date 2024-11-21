import random
import sympy
import customtkinter
import socket
import threading
import ast
import json

# These will be updated with values from server
q = None
g = None

# Networking setup
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

def gen_key(q):
    key = random.randint(2, q - 1)
    while sympy.gcd(q, key) != 1:
        key = random.randint(2, q - 1)
    return key

def power(a, b, c):
    x = 1
    y = a
    while b > 0:
        if b % 2 != 0:
            x = (x * y) % c
        y = (y * y) % c
        b = int(b / 2)
    return x % c

def encrypt_number(msg, q, h, g):
    """Encrypt a single number message"""
    k = gen_key(q)
    c1 = power(g, k, q)
    s = power(h, k, q)
    c2 = (msg * s) % q
    return c1, c2

def decrypt_number(c2, c1, key, q):
    """Decrypt a single number message"""
    s = power(c1, key, q)
    s_inv = pow(s, q - 2, q)
    decrypted_msg = (c2 * s_inv) % q
    return decrypted_msg

def text_to_numbers(text):
    return [ord(c) for c in text]

def numbers_to_text(numbers):
    return ''.join(chr(n) for n in numbers)

def encrypt_text_or_number(message, q, h, g):
    """Encrypt either a text or a number message"""
    if isinstance(message, int):
        # If message is a number, encrypt directly
        return [encrypt_number(message, q, h, g)]
    else:
        # If message is text, convert to numbers and encrypt each character
        numbers = text_to_numbers(message)
        return [encrypt_number(number, q, h, g) for number in numbers]

def decrypt_message(encrypted_message, key, q):
    """Decrypt either a single number or a list of encrypted characters"""
    try:
        # Check if it's a single encrypted number
        if len(encrypted_message) == 1 and isinstance(encrypted_message[0], tuple):
            return decrypt_number(encrypted_message[0][1], encrypted_message[0][0], key, q)
        
        # If it's a list of encrypted characters, decrypt each
        decrypted_numbers = [decrypt_number(c2, c1, key, q) for c1, c2 in encrypted_message]
        return numbers_to_text(decrypted_numbers)
    except Exception as e:
        print(f"Erreur de déchiffrement: {e}")
        return "Echec du déchiffrement"

def connect_to_server(host, port, app):
    try:
        client_socket.connect((host, port))
        print("Connecté au serveur")
        
        # Start a thread to handle incoming messages
        receive_thread = threading.Thread(target=receive_from_server, args=(app,))
        receive_thread.daemon = True
        receive_thread.start()
        
    except Exception as e:
        print(f"Erreur de connexion: {e}")

def send_public_key(public_key):
    """Send public key to server"""
    key_data = {
        'type': 'public_key',
        'public_key': public_key
    }
    try:
        client_socket.sendall(json.dumps(key_data).encode())
        print(f"Clé publique envoyée au serveur : {public_key}")
    except Exception as e:
        print(f"Erreur lors de l'envoi de la clé publique : {e}")

def send_message(encrypted_message):
    """Send encrypted message to server"""
    message_data = {
        'type': 'message',
        'content': encrypted_message
    }
    try:
        client_socket.sendall(json.dumps(message_data).encode())
    except Exception as e:
        print(f"Erreur lors de l'envoi du message : {e}")

def receive_from_server(app):
    while True:
        try:
            data = client_socket.recv(4096).decode()
            if not data:
                break
            
            message_data = json.loads(data)
            
            if message_data['type'] == 'primes':
                # Update global primes
                global q, g
                q = message_data['q']
                g = message_data['g']
                print(f"Nombres premiers - q: {q}, g: {g}")
                
                # Initialize keys and send public key to server
                app.initialize_keys()
                
            elif message_data['type'] == 'public_key':
                # Update other client's public key
                public_key = message_data['public_key']
                app.update_other_public_key(public_key)
                print(f"Clé publique de l'autre client : {public_key}")
                
            elif message_data['type'] == 'message':
                # Handle encrypted message
                encrypted_message = message_data['content']
                encrypted_list = ast.literal_eval(encrypted_message)
                decrypted_message = decrypt_message(encrypted_list, app.private_key, q)
                # Use after to schedule GUI updates from other threads
                app.after(0, lambda: app.chat_frame.add_message(str(decrypted_message), 
                                                             encrypted_message, 
                                                             "reçu"))
                
        except Exception as e:
            print(f"Erreur de réception du message : {e}")
            break

class MessageBubble(customtkinter.CTkFrame):
    def __init__(self, master, clear_text, encrypted_text, message_type="sent", **kwargs):
        super().__init__(master, fg_color="gray20" if message_type == "sent" else "gray30", **kwargs)
        
        self.grid_columnconfigure(0, weight=1)
        
        self.clear_text = clear_text
        self.encrypted_text = encrypted_text
        self.message_type = message_type
        self.showing_encrypted = True
        
        # Message content
        self.message_label = customtkinter.CTkLabel(
            self,
            text=f"{'Vous ' if message_type == 'sent' else 'Ami'} : {(clear_text if message_type == 'sent' else encrypted_text)}",
            wraplength=350,
            justify="left",
            text_color="white",
            fg_color="transparent",
        )
        self.message_label.grid(row=0, column=0, padx=5, pady=(5,0), sticky="w")
        
        # Toggle button
        self.toggle_button = customtkinter.CTkButton(
            self,
            text="Déchiffrer",
            command=self.toggle_display,
            width=100,
            height=25
        )
        self.toggle_button.grid(row=1, column=0, padx=5, pady=5, sticky="e")

    def toggle_display(self):
        self.showing_encrypted = not self.showing_encrypted
        if self.showing_encrypted:
            self.message_label.configure(
                text=f"{'Vous' if self.message_type == 'sent' else 'Ami'} (chiffré) : {self.encrypted_text}"
            )
            self.toggle_button.configure(text="Déchiffrer")
        else:
            self.message_label.configure(
                text=f"{'Vous' if self.message_type == 'sent' else 'Ami'}: {self.clear_text}"
            )
            self.toggle_button.configure(text="Chiffrer")

class ChatFrame(customtkinter.CTkScrollableFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="gray10")
        self.grid_columnconfigure(0, weight=1)
        self.messages = []

    def add_message(self, clear_text, encrypted_text, message_type="sent"):
        msg_bubble = MessageBubble(
            self, 
            clear_text, 
            encrypted_text, 
            message_type=message_type
        )
        msg_bubble.grid(row=len(self.messages), column=0, padx=10, pady=5, sticky="ew")
        self.messages.append(msg_bubble)
        
        # Force update and scroll to bottom
        self.update_idletasks()
        self._parent_canvas.yview_moveto(1.0)

class SendFrame(customtkinter.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        
        self.master = master
        self.grid_columnconfigure(0, weight=1)
        
        # Key info display
        self.key_info_label = customtkinter.CTkLabel(
            self,
            text="En attente d'échanges...",
            justify="left",
            wraplength=700
        )
        self.key_info_label.grid(row=0, column=0, padx=10, pady=(5,0), sticky="w")
        
        # Text input
        self.text_input = customtkinter.CTkTextbox(
            self,
            height=100,
            fg_color="gray20"
        )
        self.text_input.grid(row=1, column=0, padx=10, pady=10, sticky="ew")
        
        # Send button
        self.send_button = customtkinter.CTkButton(
            self,
            text="Envoyer",
            command=self.send_message,
            state="disabled"
        )
        self.send_button.grid(row=2, column=0, padx=10, pady=(0,10), sticky="e")

    def update_key_info(self):
        self.key_info_label.configure(
            text=f"Mes clés - Publique : {self.master.public_key}, Privée: {self.master.private_key}\n" +
                 f"Clé publique de l'ami : {self.master.other_public_key}"
        )
        self.send_button.configure(
            state="normal" if self.master.other_public_key else "disabled"
        )
    
    def send_message(self):
        input_text = self.text_input.get("1.0", 'end-1c').strip()
        if input_text and self.master.other_public_key:
            try:
                # Try to convert to int if possible, otherwise treat as text
                try:
                    numeric_input = int(input_text)
                    encrypted_msg = encrypt_text_or_number(numeric_input, q, self.master.other_public_key, g)
                except ValueError:
                    encrypted_msg = encrypt_text_or_number(input_text, q, self.master.other_public_key, g)
                
                encrypted_msg_str = str(encrypted_msg)
                
                self.master.chat_frame.add_message(input_text, encrypted_msg_str, "sent")
                self.text_input.delete("1.0", "end")
                send_message(encrypted_msg_str)
                
            except Exception as e:
                print(f"Erreur lors de l'envoi du message : {e}")

class ChatApp(customtkinter.CTk):
    def __init__(self):
        super().__init__()
        
        # Setup window
        customtkinter.set_appearance_mode("dark")
        customtkinter.set_default_color_theme("blue")
        
        self.title("Chiffrement - Déchiffrement ElGammal")
        self.geometry("800x600")
        self.configure(fg_color="gray10")
        
        # Configure grid
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # Initialize keys
        self.private_key = None
        self.public_key = None
        self.other_public_key = None
        
        # Create frames
        self.chat_frame = ChatFrame(self)
        self.chat_frame.grid(row=0, column=0, padx=20, pady=(20,10), sticky="nsew")
        
        self.send_frame = SendFrame(self)
        self.send_frame.grid(row=1, column=0, padx=20, pady=(0,20), sticky="ew")
    
    def initialize_keys(self):
        self.private_key = gen_key(q)
        self.public_key = power(g, self.private_key, q)
        
        print(f"Initialisation - Clé privée : {self.private_key}")
        print(f"Initialisation - Clé publique : {self.public_key}")
        
        self.send_frame.update_key_info()
        send_public_key(self.public_key)
    
    def update_other_public_key(self, public_key):
        self.other_public_key = public_key
        self.send_frame.update_key_info()

if __name__ == "__main__":
    app = ChatApp()
    
    server_host = "127.0.0.1"
    server_port = 12345
    
    connect_to_server(server_host, server_port, app)
    
    app.mainloop()