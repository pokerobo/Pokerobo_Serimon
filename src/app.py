import sys
import serial
import serial.tools.list_ports
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QComboBox, QTextEdit, QLineEdit, QMessageBox
)
from PyQt6.QtCore import QThread, pyqtSignal


class SerialReader(QThread):
    data_received = pyqtSignal(str)

    def __init__(self, serial_port):
        super().__init__()
        self.serial_port = serial_port
        self.running = True

    def run(self):
        while self.running:
            if self.serial_port.in_waiting:
                try:
                    line = self.serial_port.readline().decode('utf-8').strip()
                    self.data_received.emit(line)
                except Exception:
                    pass

    def stop(self):
        self.running = False
        self.quit()
        self.wait()


class SerialApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pokerobo Serimon")
        self.serial_port = None
        self.reader_thread = None

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Cổng COM
        port_layout = QHBoxLayout()
        self.port_label = QLabel("Port:")
        self.port_combo = QComboBox()
        self.port_combo.addItems(self.get_serial_ports())

        self.connect_button = QPushButton("Connect")
        self.connect_button.clicked.connect(self.toggle_connection)

        port_layout.addWidget(self.port_label)
        port_layout.addWidget(self.port_combo)
        port_layout.addWidget(self.connect_button)
        layout.addLayout(port_layout)

        # Vùng hiển thị
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        layout.addWidget(self.output_text)

        # Gửi dữ liệu
        send_layout = QHBoxLayout()
        self.input_line = QLineEdit()
        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(self.send_data)
        send_layout.addWidget(self.input_line)
        send_layout.addWidget(self.send_button)
        layout.addLayout(send_layout)

        self.setLayout(layout)

    def get_serial_ports(self):
        ports = serial.tools.list_ports.comports()
        return [port.device for port in ports]

    def toggle_connection(self):
        if self.serial_port and self.serial_port.is_open:
            self.disconnect_serial()
        else:
            self.connect_serial()

    def connect_serial(self):
        port = self.port_combo.currentText()
        try:
            self.serial_port = serial.Serial(port, baudrate=57600, timeout=1)
            self.reader_thread = SerialReader(self.serial_port)
            self.reader_thread.data_received.connect(self.display_data)
            self.reader_thread.start()
            self.connect_button.setText("Disconnect")
        except serial.SerialException as e:
            QMessageBox.critical(self, "Error:", str(e))

    def disconnect_serial(self):
        if self.reader_thread:
            self.reader_thread.stop()
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()
        self.connect_button.setText("Connect")

    def send_data(self):
        if self.serial_port and self.serial_port.is_open:
            data = self.input_line.text()
            if data:
                self.serial_port.write((data + '\n').encode())

    def display_data(self, data):
        self.output_text.append(data)

    def closeEvent(self, event):
        self.disconnect_serial()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SerialApp()
    window.show()
    sys.exit(app.exec())
