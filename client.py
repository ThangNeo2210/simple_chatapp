import tkinter as tk
from tkinter import scrolledtext, ttk, messagebox, simpledialog
import socket
import json
import threading
from datetime import datetime

class ChatClient:
    def __init__(self, host='127.0.0.1', port=5555):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.host = host
        self.port = port
        
       
        self.username = self.get_username()
        
        
        self.setup_gui()
        
        
        self.connect_to_server()

    def get_username(self):
        root = tk.Tk()
        root.withdraw()
        username = ""
        while not username:
            username = simpledialog.askstring("Username", "Enter your username:")
            if username is None:
                exit()
        return username

    def setup_gui(self):
        self.root = tk.Tk()
        self.root.title(f"Chat App - {self.username}")
        self.root.geometry("1000x700")
        self.root.configure(bg='#f0f0f0')

        self.main_frame = ttk.Frame(self.root, padding="20")
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        self.chat_frame = ttk.Frame(self.main_frame)
        self.chat_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))

        self.chat_display = scrolledtext.ScrolledText(
            self.chat_frame,
            wrap=tk.WORD,
            font=('Helvetica', 11),
            bg='white',
            padx=20,
            pady=20
        )
        self.chat_display.pack(fill=tk.BOTH, expand=True)

        self.chat_display.tag_configure('other', foreground='#2B5278')
        self.chat_display.tag_configure('you', foreground='#1B8C00')
        self.chat_display.tag_configure('server', foreground='#AB0000')
        self.chat_display.tag_configure('time', foreground='#666666', font=('Helvetica', 9))
        
        self.chat_display.tag_configure('your_bubble', background='#DCF8C6', rmargin=150)
        self.chat_display.tag_configure('other_bubble', background='#E8E8E8', lmargin1=150)

        self.bottom_frame = ttk.Frame(self.main_frame)
        self.bottom_frame.pack(fill=tk.X, pady=(0, 10))

        self.message_input = ttk.Entry(
            self.bottom_frame,
            style='Chat.TEntry',
            width=90
        )
        self.message_input.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 20))
        self.message_input.focus()

        self.send_button = ttk.Button(
            self.bottom_frame,
            text="Send",
            command=self.send_message,
            style='Chat.TButton',
            width=15
        )
        self.send_button.pack(side=tk.RIGHT)

        style = ttk.Style()
        style.configure('Chat.TEntry', padding=10)
        style.configure('Chat.TButton', padding=10)

    def display_message(self, sender, message, timestamp):
        self.chat_display.config(state='normal')
        
        
        if self.chat_display.index('end-1c') != '1.0':
            self.chat_display.insert(tk.END, '\n')

        
        self.chat_display.insert(tk.END, f"{timestamp}\n", 'time')

        
        if sender == "Server":
            self.chat_display.insert(tk.END, f"{message}\n", 'server')
        else:
            
            if sender == self.username:
                tag = 'your_bubble'
                sender_tag = 'you'
                self.chat_display.insert(tk.END, f"You: ", sender_tag)
            else:
                tag = 'other_bubble'
                sender_tag = 'other'
                self.chat_display.insert(tk.END, f"{sender}: ", sender_tag)

            
            self.chat_display.insert(tk.END, f"{message}\n", tag)

        self.chat_display.config(state='disabled')
        self.chat_display.see(tk.END)

    def send_message(self):
        message = self.message_input.get().strip()
        if message:
            current_time = datetime.now().strftime("%I:%M %p")
            
           
            self.display_message(self.username, message, current_time)
            
           
            message_data = {
                "type": "message",
                "sender": self.username,
                "message": message
            }
            try:
                self.socket.send(json.dumps(message_data).encode())
                self.message_input.delete(0, tk.END)
            except:
                messagebox.showerror("Error", "Could not send message")

    def receive_messages(self):
        while True:
            try:
                data = self.socket.recv(1024).decode()
                if not data:
                    break
                
                message_data = json.loads(data)
                
                if message_data["type"] == "history":
                    
                    for msg in message_data["messages"]:
                        if msg["sender"] != self.username:  # Only show others' messages from history
                            self.display_message(msg["sender"], msg["message"], msg["time"])
                elif message_data["sender"] != self.username:  # Don't show our own messages twice
                    
                    self.display_message(
                        message_data["sender"],
                        message_data["message"],
                        message_data["time"]
                    )
                    
            except Exception as e:
                print(f"Error receiving message: {e}")
                messagebox.showerror("Error", "Lost connection to server")
                self.socket.close()
                break

    def connect_to_server(self):
        try:
            self.socket.connect((self.host, self.port))
            
            # Send username to server
            username_data = json.dumps({"type": "username", "username": self.username})
            self.socket.send(username_data.encode())
            
            # Start thread to receive messages
            receive_thread = threading.Thread(target=self.receive_messages)
            receive_thread.daemon = True
            receive_thread.start()
            
        except Exception as e:
            messagebox.showerror("Connection Error", f"Could not connect to server: {e}")
            exit()

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    client = ChatClient()
    client.run()