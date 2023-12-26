import socket
import psutil
import sys
import threading
import json
import time
import os
import platform  # New import
from PyQt5 import QtWidgets, QtGui, Qt
from PyQt5.QtWidgets import QStyle, QInputDialog
from plyer import notification  # for desktop notifications

# Constants
CONFIG_FILE = "config.json"
DEFAULT_SERVER_IP = "127.0.0.1"
SERVER_PORT = 7441

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as file:
            return json.load(file)
    else:
        return {"server_ip": DEFAULT_SERVER_IP}

def save_config(config):
    with open(CONFIG_FILE, "w") as file:
        json.dump(config, file)

def get_system_info():
    hostname = socket.gethostname()
    ip_address = socket.gethostbyname(hostname)
    try:
        # Try to get a more accurate IP if possible (e.g., if behind a router)
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip_address = socket.gethostbyname(hostname)
        s.close()
    except:
        pass
    user_name = os.getlogin()  
    cpu_percent = psutil.cpu_percent()
    ram_percent = psutil.virtual_memory().percent

    return f"IP Address: {ip_address}, Hostname: {hostname}, Active User: {user_name}, CPU: {cpu_percent}%, RAM: {ram_percent}%"

def send_system_health_data(server_ip, server_port, interval):
    while True: 
        try:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect((server_ip, server_port))
            health_data = get_system_info()
            client.sendall(health_data.encode())
            notify("Connected", f"Successfully sent data to {server_ip}")
        except Exception as e:
            notify("Connection Failed", f"Error: {e}")
        finally:
            client.close()
        time.sleep(interval)  

def notify(title, message):
    notification.notify(
        title=title,
        message=message,
        app_name='System Monitor Client'
    )

class SystemTrayIcon(QtWidgets.QSystemTrayIcon):
    def __init__(self, parent=None):
        self.config = load_config()
        icon = QtWidgets.QApplication.style().standardIcon(QStyle.SP_ComputerIcon)
        QtWidgets.QSystemTrayIcon.__init__(self, icon, parent)
        self.setToolTip(f'System Monitor Client')
        menu = QtWidgets.QMenu(parent)
        open_action = menu.addAction("Send Data")
        open_action.triggered.connect(self.on_open)
        set_ip_action = menu.addAction("Set Server IP")
        set_ip_action.triggered.connect(self.on_set_ip)
        exit_action = menu.addAction("Exit")
        exit_action.triggered.connect(QtWidgets.qApp.quit)
        self.setContextMenu(menu)

    def on_open(self):
        interval, okPressed = QInputDialog.getInt(None, "Set Interval", "Interval (seconds):", value=30, min=1, max=3600)
        if okPressed:
            self.config['interval'] = interval
            save_config(self.config)
        threading.Thread(target=send_system_health_data, args=(self.config['server_ip'], SERVER_PORT, self.config.get('interval', 30))).start()

    def on_set_ip(self):
        ip, okPressed = QInputDialog.getText(None, "Set Server IP","Server IP:", Qt.QLineEdit.Normal, self.config['server_ip'])
        if okPressed and ip != '':
            self.config['server_ip'] = ip
            save_config(self.config)
            notify("Server IP Updated", f"New server IP: {ip}")

def main():
    app = QtWidgets.QApplication(sys.argv)
    w = QtWidgets.QWidget()
    tray_icon = SystemTrayIcon(w)
    tray_icon.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
