import socket
import threading
import json
from datetime import datetime
import queue

class ChatServer:
    def __init__(self, host='127.0.0.1', port=5555):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.clients = {}
        self.message_queue = queue.Queue()
        self.client_locks = {}
        
        self.message_history = [
            {"sender": "John", "message": "Hey there!", "time": "10:30 AM"},
            {"sender": "Alice", "message": "Hi! How are you?", "time": "10:31 AM"},
            {"sender": "John", "message": "I'm doing great, thanks!", "time": "10:32 AM"},
        ]
        
        self.history_lock = threading.Lock()
        
        self.message_processor = threading.Thread(target=self.process_messages)
        self.message_processor.daemon = True
        self.message_processor.start()

    def start(self):
        try:
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            print(f"Server started on {self.host}:{self.port}")

            accept_thread = threading.Thread(target=self.accept_connections)
            accept_thread.daemon = True
            accept_thread.start()

            while True:
                cmd = input()
                if cmd.lower() == 'quit':
                    break
                
        except Exception as e:
            print(f"Server error: {e}")
        finally:
            self.cleanup()

    def accept_connections(self):
        while True:
            try:
                client_socket, address = self.server_socket.accept()
                print(f"New connection from {address}")
                
                init_thread = threading.Thread(
                    target=self.initialize_client,
                    args=(client_socket, address)
                )
                init_thread.start()
            except:
                break

    def initialize_client(self, client_socket, address):
        try:
            username_data = json.loads(client_socket.recv(1024).decode())
            username = username_data.get("username", f"User_{address[1]}")
            
            self.client_locks[username] = threading.Lock()
            
            with self.client_locks[username]:
                self.clients[username] = {
                    'socket': client_socket,
                    'address': address,
                    'last_active': datetime.now()
                }
            
            self.send_message_history(client_socket)
            
            join_message = {
                "type": "message",
                "sender": "Server",
                "message": f"{username} has joined the chat",
                "time": datetime.now().strftime("%I:%M %p")
            }
            self.message_queue.put((join_message, client_socket))
            
            receive_thread = threading.Thread(
                target=self.handle_client,
                args=(username,)
            )
            receive_thread.daemon = True
            receive_thread.start()
            
        except Exception as e:
            print(f"Error initializing client: {e}")
            client_socket.close()

    def process_messages(self):
        while True:
            try:
                message_data, exclude_socket = self.message_queue.get()
                self.broadcast_message(message_data, exclude_socket)
                self.message_queue.task_done()
            except:
                continue

    def send_message_history(self, client_socket):
        with self.history_lock:
            history_data = json.dumps({"type": "history", "messages": self.message_history})
            try:
                client_socket.send(history_data.encode())
            except Exception as e:
                print(f"Error sending history: {e}")

    def broadcast_message(self, message_data, exclude_socket=None):
        for username, client_info in list(self.clients.items()):
            if client_info['socket'] != exclude_socket:
                try:
                    with self.client_locks[username]:
                        client_info['socket'].send(json.dumps(message_data).encode())
                except:
                    self.remove_client(username)

    def handle_client(self, username):
        client_info = self.clients.get(username)
        if not client_info:
            return

        client_socket = client_info['socket']
        
        while True:
            try:
                message = client_socket.recv(1024).decode()
                if not message:
                    break
                
                message_data = json.loads(message)
                message_data["time"] = datetime.now().strftime("%I:%M %p")
                
                with self.client_locks[username]:
                    self.clients[username]['last_active'] = datetime.now()
                
                if message_data["type"] == "message":
                    with self.history_lock:
                        self.message_history.append(message_data)
                
                self.message_queue.put((message_data, client_socket))
                
            except:
                break
        
        self.remove_client(username)

    def remove_client(self, username):
        if username in self.clients:
            with self.client_locks[username]:
                client_socket = self.clients[username]['socket']
                client_socket.close()
                del self.clients[username]
                del self.client_locks[username]
            
            leave_message = {
                "type": "message",
                "sender": "Server",
                "message": f"{username} has left the chat",
                "time": datetime.now().strftime("%I:%M %p")
            }
            self.message_queue.put((leave_message, None))

    def cleanup(self):
        print("Shutting down server...")
        for username in list(self.clients.keys()):
            self.remove_client(username)
        self.server_socket.close()

if __name__ == "__main__":
    server = ChatServer()
    server.start()