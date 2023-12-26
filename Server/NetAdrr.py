from flask import Flask, render_template
import socket
import threading
from datetime import datetime
from flask import jsonify

app = Flask(__name__)

# Your Server class remains mostly unchanged
class Server:
    def __init__(self, host='0.0.0.0', port=7441):
        self.host = host
        self.port = port
        self.active_computers = {}  # Storing more detailed data

    def start_server(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind((self.host, self.port))
        server.listen(5)
        print(f"Server listening on {self.host}:{self.port}")

        while True:
            client, addr = server.accept()
            print(f"Connected by {addr}")
            try:
                data = client.recv(1024).decode()
                if data:  # Ensure data is not empty
                    data_dict = dict(item.split(": ") for item in data.split(", "))
                    self.active_computers[addr[0]] = data_dict
                    print(f"Received: {data}")
                else:
                    print(f"No data received from {addr}")
            except Exception as e:
                print(f"Error receiving data: {e}")
            finally:
                client.close()

            # Debug print to show active computers
            print(f"Active Computers: {self.active_computers}")

server = Server()

# Flask routes
@app.route('/')
def index():
    return render_template('index.html', computers=server.active_computers)

@app.route('/fetch_data')
def fetch_data():
    return jsonify(server.active_computers)

def start_server_thread():
    server_thread = threading.Thread(target=server.start_server, daemon=True)
    server_thread.start()

if __name__ == '__main__':
    start_server_thread()
    app.run(debug=True)
