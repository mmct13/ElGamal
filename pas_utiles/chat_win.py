import random
import customtkinter
from PIL import Image

from crypt_elgammal import encrypt, gen_key, power

# Cadre pour l'envoi de messages
class SendFrame(customtkinter.CTkFrame):
    def __init__(self, master, chat_frame):
        super().__init__(master)
        self.chat_frame = chat_frame
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Label et champ de texte pour le message clair
        self.text_label = customtkinter.CTkLabel(self, text="Entrez le message à chiffrer :", justify="center")
        self.text_label.grid(row=0, column=0, padx=10, pady=(10, 0), sticky="w")

        self.text_clair = customtkinter.CTkTextbox(self, height=100)
        self.text_clair.grid(row=1, column=0, padx=10, pady=(10, 0), sticky="ew", columnspan=2)

        # Bouton pour chiffrer le message
        self.create_button('change_icon.png', "Chiffrer", self.update_output, "e", 2)

        # Label et champ pour afficher le message crypté
        self.crypt_text_label = customtkinter.CTkLabel(self, text="Message crypté :", justify="center")
        self.crypt_text_label.grid(row=3, column=0, padx=10, pady=(10, 0), sticky="w")

        self.output = customtkinter.CTkLabel(self, text="", height=100, fg_color="white", text_color="black")
        self.output.grid(row=4, column=0, padx=10, pady=(10, 0), sticky="ew", columnspan=2)

        # Bouton pour envoyer le message crypté dans la ChatFrame
        self.create_button('send_icon.png', "Envoyer", self.send_message, "e", 5)




    def retrieve_input(self):
        return self.text_clair.get("1.0", 'end-1c')

    def update_output(self):
        # Simule le chiffrement du texte clair
        input_text = self.retrieve_input()
       
        self.output.configure(text=input_text)

    def send_message(self):
        # Envoie le message crypté à la ChatFrame
        crypted_text = self.output.cget("text")
        self.chat_frame.add_message(crypted_text)
        if crypted_text == "ok":
            self.chat_frame.receive_message()

    def create_button(self, image_path, text, callback, stick, row):
        send_icon = customtkinter.CTkImage(light_image=Image.open(image_path), size=(20, 20))
        button = customtkinter.CTkButton(self, text=text, image=send_icon, command=callback)
        button.grid(row=row, column=1, padx=10, pady=10, sticky=stick)
        button.configure(font=("Poppins Sans MS", 15, "bold"))

# Cadre pour afficher les messages dans une zone défilante
class ChatFrame(customtkinter.CTkScrollableFrame):
    def __init__(self, master):
        super().__init__(master)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.config(height=500)

    def add_message(self, message_text):
        # Crée un cadre pour chaque message envoyé
        msg_frame = customtkinter.CTkFrame(self, fg_color='white', corner_radius=10)
        msg_frame.grid(row=self.grid_size()[1], column=0, padx=10, pady=(10, 0), sticky="ew")
        crypted_msg_output = customtkinter.CTkLabel(
            msg_frame, wraplength=400, text=message_text, fg_color='white', text_color="black", justify="left"
        )
        crypted_msg_output.grid(row=0, column=0, padx=20, pady=(10, 0), sticky="we", columnspan=2)

    def receive_message(self):
        # Affiche un message reçu
        msg_frame = customtkinter.CTkFrame(self, fg_color='#bfd0e5', corner_radius=10)
        msg_frame.grid(row=self.grid_size()[1], column=0, padx=10, pady=(10, 0), sticky="ew")

        crypted_msg_output = customtkinter.CTkLabel(
            msg_frame, wraplength=400, text="received", fg_color='#bfd0e5', text_color="black"
        )
        crypted_msg_output.grid(row=0, column=0, padx=10, pady=(10, 0), sticky="we", columnspan=2)

        button = customtkinter.CTkButton(msg_frame, text="dechiffrer", command=self.decriffre)
        button.grid(row=1, column=0, padx=10, pady=10, sticky="w")
        button.configure(font=("Poppins Sans MS", 10, "bold"))

    def decriffre(self):
        # Affiche un message déchiffré
        label = customtkinter.CTkLabel(
            self, wraplength=400, text="received", fg_color='#9fbee6', font=("Poppins Sans MS", 10, "bold"),
            text_color="black"
        )
        label.grid(row=self.grid_size()[1], column=0, padx=10, pady=(10, 0), sticky="w", columnspan=2)

# Fenêtre principale de l'application de chat
class ChatWindows(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        self.title("Cryptage-Decryptage ElGammal")
        self.geometry("900x750")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width // 2) - (900 // 2)
        y = (screen_height // 2) - (750 // 2)
        self.geometry(f"900x750+{x}+{y}")

        self.chat_frame = ChatFrame(self)
        self.chat_frame.grid(row=0, column=0, padx=30, pady=(10, 0), sticky="ew")

        self.send_frame = SendFrame(self, self.chat_frame)
        self.send_frame.grid(row=1, column=0, padx=30, pady=(10, 0), sticky="ew")

# Exécution de l'application
app = ChatWindows()
app.mainloop()
