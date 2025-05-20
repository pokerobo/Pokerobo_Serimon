import sys
import serial
import serial.tools.list_ports
import time
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QComboBox, QLineEdit, QPlainTextEdit, QTabWidget, QLabel
)
from PyQt6.QtCore import QTimer
import pyqtgraph as pg

class SerialMonitor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pokerobo Serimon")
        self.resize(800, 600)

        self.serial = None
        self.last_read_time = time.time()
        self.line_count = 0
        self.byte_count = 0

        self.init_ui()
        self.timer = QTimer()
        self.timer.timeout.connect(self.read_serial)
        self.timer.start(50)

        self.stats_timer = QTimer()
        self.stats_timer.timeout.connect(self.update_stats)
        self.stats_timer.start(1000)

    def init_ui(self):
        self.tabs = QTabWidget()
        self.console_tab = QWidget()
        self.diagram_tab = QWidget()
        self.tabs.addTab(self.console_tab, "Console")
        self.tabs.addTab(self.diagram_tab, "Diagram")

        # ==== Top control layout ====
        self.port_cb = QComboBox()
        self.baud_cb = QComboBox()
        self.baud_cb.addItems(["9600", "19200", "38400", "57600", "115200", "250000"])
        self.connect_btn = QPushButton("Connect")
        self.connect_btn.clicked.connect(self.toggle_serial)
        self.refresh_ports()

        top_layout = QHBoxLayout()
        top_layout.addWidget(QLabel("COM Port:"))
        top_layout.addWidget(self.port_cb)
        top_layout.addWidget(QLabel("Baudrate:"))
        top_layout.addWidget(self.baud_cb)
        top_layout.addWidget(self.connect_btn)

        # ==== Console tab ====
        self.console_output = QPlainTextEdit()
        self.console_output.setReadOnly(True)
        self.console_input = QLineEdit()
        self.console_input.returnPressed.connect(self.send_serial)

        console_layout = QVBoxLayout()
        console_layout.addLayout(top_layout)
        console_layout.addWidget(self.console_output)
        console_layout.addWidget(self.console_input)
        self.console_tab.setLayout(console_layout)

        # ==== Diagram tab ====
        self.line_plot = pg.PlotWidget(title="Messages per second")
        self.byte_plot = pg.PlotWidget(title="Bytes per second")
        self.line_curve = self.line_plot.plot(pen='g')
        self.byte_curve = self.byte_plot.plot(pen='b')
        self.line_data = []
        self.byte_data = []

        diagram_layout = QVBoxLayout()
        diagram_layout.addWidget(self.line_plot)
        diagram_layout.addWidget(self.byte_plot)
        self.diagram_tab.setLayout(diagram_layout)

        self.setCentralWidget(self.tabs)

    def refresh_ports(self):
        self.port_cb.clear()
        ports = serial.tools.list_ports.comports()
        for port in ports:
            self.port_cb.addItem(port.device)

    def toggle_serial(self):
        if self.serial and self.serial.is_open:
            self.serial.close()
            self.serial = None
            self.connect_btn.setText("Connect")
            self.console_output.appendPlainText("[Disconnected]")
        else:
            port = self.port_cb.currentText()
            baudrate = int(self.baud_cb.currentText())
            try:
                self.serial = serial.Serial(port, baudrate, timeout=0.1)
                self.connect_btn.setText("Disconnect")
                self.console_output.appendPlainText(f"[Connected to {port} at {baudrate} bps]")
            except Exception as e:
                self.console_output.appendPlainText(f"[Error opening port: {e}]")
                self.serial = None

    def send_serial(self):
        if self.serial and self.serial.is_open:
            text = self.console_input.text()
            self.serial.write((text + '\n').encode())
            self.console_input.clear()

    def read_serial(self):
        if self.serial and self.serial.is_open:
            try:
                while self.serial.in_waiting:
                    line = self.serial.readline().decode(errors='ignore').strip()
                    self.console_output.appendPlainText(line)
                    self.line_count += 1
                    self.byte_count += len(line.encode())
            except Exception as e:
                self.console_output.appendPlainText(f"[Read error: {e}]")

    def update_stats(self):
        self.line_data.append(self.line_count)
        self.byte_data.append(self.byte_count)
        self.line_data = self.line_data[-60:]
        self.byte_data = self.byte_data[-60:]
        self.line_curve.setData(self.line_data)
        self.byte_curve.setData(self.byte_data)
        self.line_count = 0
        self.byte_count = 0

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = SerialMonitor()
    win.show()
    sys.exit(app.exec())
