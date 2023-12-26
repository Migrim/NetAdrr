import sys
import socket
import threading
from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtCore import pyqtSignal, QObject, Qt
from PyQt5.QtWidgets import QLabel, QVBoxLayout, QHBoxLayout
from datetime import datetime
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

class Server(QObject):
    new_message = pyqtSignal(str)
    update_computers = pyqtSignal(dict)

    def __init__(self, host='0.0.0.0', port=7441):
        super().__init__()
        self.host = host
        self.port = port
        self.active_computers = {}  # Storing more detailed data

    def start_server(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind((self.host, self.port))
        server.listen(5)
        self.new_message.emit(f"Server listening on {self.host}:{self.port}")

        while True:
            client, addr = server.accept()
            self.active_computers[addr[0]] = datetime.now()
            self.new_message.emit(f"Connected by {addr}")
            data = client.recv(1024).decode()
            # Assume data format is "IP Address: ..., Hostname: ..., Active User: ..., CPU: ..., RAM: ..."
            data_dict = dict(item.split(": ") for item in data.split(", "))
            self.active_computers[addr[0]] = data_dict  # Store detailed data
            self.new_message.emit(f"Received: {data}")
            self.update_computers.emit(self.active_computers)
            client.close()

class ServerGUI(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.server = Server()
        self.server.new_message.connect(self.update_terminal)
        self.server.update_computers.connect(self.update_computers)
        self.details_tabs = {}

    def initUI(self):
        self.setGeometry(100, 100, 600, 400)
        self.setWindowTitle('Server Monitoring - Dark Mode')
        self.setStyleSheet("""
            QWidget {
                background-color: #34495e;
                color: #ecf0f1;
            }
            QTextEdit, QListWidget {
                background-color: #2c3e50;
            }
            QTabWidget::tab-bar {
                color: #ecf0f1;
            }
            QTabBar::tab {
                background: #34495e;
                color: #ecf0f1;
            }
            QTabBar::tab:selected {
                background: #2c3e50;
            }
        """)

        # Layouts
        layout = QtWidgets.QVBoxLayout()
        tab_layout = QtWidgets.QTabWidget()

        self.tab_layout = QtWidgets.QTabWidget()

        # Terminal Tab
        self.terminal = QtWidgets.QTextEdit()
        self.terminal.setReadOnly(True)
        self.tab_layout.addTab(self.terminal, "Terminal Messages")

        # Computers Tab
        self.computers = QtWidgets.QListWidget()
        self.computers.itemClicked.connect(self.display_computer_details)
        self.tab_layout.addTab(self.computers, "Computers")

        # Set Layout
        layout.addWidget(self.tab_layout)
        self.setLayout(layout)

    def update_terminal(self, message):
        self.terminal.append(message)

    def update_computers(self, active_computers):
        self.computers.clear()
        for ip, data_dict in active_computers.items():

            item = QtWidgets.QListWidgetItem(f"{ip}")
            self.computers.addItem(item)

    def display_computer_details(self, item):
        ip = item.text()
        data_dict = self.server.active_computers.get(ip, {})

        if ip not in self.details_tabs:
            details_tab = QtWidgets.QWidget()
            self.details_tabs[ip] = details_tab
            details_layout = QtWidgets.QVBoxLayout()

            for key, value in data_dict.items():
                label = QtWidgets.QLabel(f"{key}: {value}")
                details_layout.addWidget(label)

            # Plot actual CPU usage data if available
            if "CPU" in data_dict:
                fig, ax = plt.subplots()
                # Process CPU data: Remove '%' and convert to float
                cpu_data = [float(cpu.strip('%')) for cpu in data_dict["CPU"].split(',')]
                ax.plot(range(len(cpu_data)), cpu_data)  
                canvas = FigureCanvas(fig)
                details_layout.addWidget(canvas)

            details_tab.setLayout(details_layout)
            index = self.tab_layout.addTab(details_tab, f"Details: {ip}")

            # Add a close button to the tab
            close_button = QtWidgets.QPushButton("x")
            close_button.setFixedSize(20, 20)
            close_button.clicked.connect(lambda: self.close_tab(index))
            self.tab_layout.tabBar().setTabButton(index, QtWidgets.QTabBar.RightSide, close_button)
        
        # Show the tab
        index = self.tab_layout.indexOf(self.details_tabs[ip])
        self.tab_layout.setCurrentIndex(index)

    def close_tab(self, index):
        # Close and remove the tab
        widget = self.tab_layout.widget(index)
        widget.deleteLater()
        self.tab_layout.removeTab(index)

def main():
    app = QtWidgets.QApplication(sys.argv)
    gui = ServerGUI()
    gui.show()

    server_thread = threading.Thread(target=gui.server.start_server, daemon=True)
    server_thread.start()

    sys.exit(app.exec_())

if __name__ == '__main__':
    main()