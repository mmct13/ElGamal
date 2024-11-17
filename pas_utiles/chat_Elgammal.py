import random
import customtkinter
from PIL import Image
import sympy

# Paramètres ElGamal partagés entre le client et le serveur
q = sympy.randprime(100, 200)  # Nombre premier q
g = sympy.randprime(2, q)  # Générateur g
server_public_key = None

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

def encrypt(msg, q, h, g):
    k = gen_key(q)
    c1 = power(g, k, q)
    s = power(h, k, q)
    c2 = (msg * s) % q
    return c1, c2

def decrypt(c2, c1, key, q):
    s = power(c1, key, q)
    s_inv = pow(s, q - 2, q)
    decrypted_msg = (c2 * s_inv) % q
    return decrypted_msg

def split_number_into_segments(number, max_value):
    segments = []
    while number > 0:
        segments.append(number % max_value)
        number //= max_value
    return segments[::-1]

def combine_segments_to_number(segments, max_value):
    number = 0
    for segment in segments:
        number = number * max_value + segment
    return number

def encrypt_number(number, q, h, g):
    segments = split_number_into_segments(number, q)
    encrypted_segments = [encrypt(segment, q, h, g) for segment in segments]
    return encrypted_segments

def decrypt_number(encrypted_segments, key, q):
    decrypted_segments = [decrypt(c2, c1, key, q) for c1, c2 in encrypted_segments]
    return combine_segments_to_number(decrypted_segments, q)

# Cadre pour l'envoi de messages
class SendFrame(customtkinter.CTkFrame):
    def __init__(self, master, chat_frame):
        super().__init__(master)
        self.chat_frame = chat_frame
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.text_label = customtkinter.CTkLabel(self, text="Entrez un nombre entier :", justify="center")
        self.text_label.grid(row=0, column=0, padx=10, pady=(10, 0), sticky="w")

        self.text_clair = customtkinter.CTkTextbox(self, height=100)
        self.text_clair.grid(row=1, column=0, padx=10, pady=(10, 0), sticky="ew", columnspan=2)

        self.create_button('change_icon.png', "Chiffrer", self.update_output, "e", 2)

        self.crypt_text_label = customtkinter.CTkLabel(self, text="Message chiffré :", justify="center")
        self.crypt_text_label.grid(row=3, column=0, padx=10, pady=(10, 0), sticky="w")

        self.output = customtkinter.CTkLabel(self, text="", height=100, fg_color="white", text_color="black")
        self.output.grid(row=4, column=0, padx=10, pady=(10, 0), sticky="ew", columnspan=2)

        self.create_button('send_icon.png', "Envoyer", self.send_message, "e", 5)
        self.create_button('decrypt_icon.png', "Déchiffrer", self.chat_frame.decriffre, "e", 6)

    def retrieve_input(self):
        try:
            return int(self.text_clair.get("1.0", 'end-1c').strip())
        except ValueError:
            return None

    def update_output(self):
        input_value = self.retrieve_input()
        if input_value is not None:
            encrypted_msg = encrypt_number(input_value, q, server_public_key, g)
            encrypted_msg_str = str(encrypted_msg)
            self.output.configure(text=encrypted_msg_str)
            print(f"Message chiffré : {encrypted_msg}")
        else:
            self.output.configure(text="Entrée invalide, entrez un nombre entier.")
            print("Erreur : Entrée invalide.")

    def send_message(self):
        crypted_text = self.output.cget("text")
        self.chat_frame.add_message(crypted_text)

    def create_button(self, image_path, text, callback, stick, row):
        button_icon = customtkinter.CTkImage(light_image=Image.open(image_path), size=(20, 20))
        button = customtkinter.CTkButton(self, text=text, image=button_icon, command=callback)
        button.grid(row=row, column=1, padx=10, pady=10, sticky=stick)
        button.configure(font=("Poppins Sans MS", 15, "bold"))

class ChatFrame(customtkinter.CTkScrollableFrame):
    def __init__(self, master, server_private_key, send_frame):
        super().__init__(master)
        self.server_private_key = server_private_key
        self.send_frame = send_frame
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.config(height=500)

    def add_message(self, message_text):
        msg_frame = customtkinter.CTkFrame(self, fg_color='white', corner_radius=10)
        msg_frame.grid(row=self.grid_size()[1], column=0, padx=10, pady=(10, 0), sticky="ew")
        crypted_msg_output = customtkinter.CTkLabel(
            msg_frame, wraplength=400, text=message_text, fg_color='white', text_color="black", justify="left"
        )
        crypted_msg_output.grid(row=0, column=0, padx=20, pady=(10, 0), sticky="we", columnspan=2)

    def decriffre(self):
        encrypted_msg = self.send_frame.output.cget("text")
        try:
            en_msg = eval(encrypted_msg.strip())
            decrypted_msg = decrypt_number(en_msg, self.server_private_key, q)
            decrypted_text = f"Nombre décrypté : {decrypted_msg}"

            label = customtkinter.CTkLabel(
                self, wraplength=400, text=decrypted_text, fg_color='#9fbee6', font=("Poppins Sans MS", 10, "bold"),
                text_color="black"
            )
            label.grid(row=self.grid_size()[1], column=0, padx=10, pady=(10, 0), sticky="w", columnspan=2)
            print(f"Valeurs décryptées : {decrypted_msg}")
        except Exception as e:
            print("Erreur de décryptage:", e)

class ChatWindows(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        self.title("Cryptage-Decryptage ElGamal")
        self.geometry("900x750")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width // 2) - (900 // 2)
        y = (screen_height // 2) - (750 // 2)
        self.geometry(f"900x750+{x}+{y}")

        self.key = gen_key(q)
        global server_public_key
        server_public_key = power(g, self.key, q)
        print(f"Clé publique du serveur: {server_public_key}")

        self.chat_frame = ChatFrame(self, self.key, None)
        self.chat_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")

        self.send_frame = SendFrame(self, self.chat_frame)
        self.send_frame.grid(row=1, column=0, padx=20, pady=20, sticky="nsew")

        self.chat_frame.send_frame = self.send_frame

if __name__ == "__main__":
    app = ChatWindows()
    app.mainloop()
