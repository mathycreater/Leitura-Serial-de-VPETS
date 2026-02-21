import serial
import serial.tools.list_ports
import threading
import tkinter as tk
from tkinter import scrolledtext
import re

class SerialCH340App:
    def __init__(self, master):
        self.master = master
        self.master.title("USB-SERIAL CH340 Interface")
        self.serial_port = None
        self.running = False
        self.stream_to_send = "V2-005E-007E-041E-141E-004E"

        # Área de log principal
        self.text_area = scrolledtext.ScrolledText(master, width=80, height=15)
        self.text_area.pack(pady=(10, 5))

        # Caixa para mostrar versão e index
        self.info_box = tk.Text(master, height=3, width=80, state=tk.DISABLED, bg="#f0f0f0", fg="blue")
        self.info_box.pack(pady=(0, 10))

        # Botões
        self.send_button = tk.Button(master, text="Enviar Stream", command=self.send_stream, state=tk.DISABLED)
        self.send_button.pack(pady=2)

        self.toggle_button = tk.Button(master, text="Desabilitar", command=self.toggle_serial)
        self.toggle_button.pack(pady=2)

        self.restart_button = tk.Button(master, text="Reiniciar", command=self.restart_serial)
        self.restart_button.pack(pady=2)

        self.detect_and_connect()

    def detect_and_connect(self):
        ports = serial.tools.list_ports.comports()
        for port in ports:
            if "USB-SERIAL CH340" in port.description:
                self.serial_port = serial.Serial(port.device, 9600, timeout=1)
                self.running = True
                self.send_button.config(state=tk.NORMAL)
                self.text_area.insert(tk.END, f"Conectado em {port.device}\n")
                threading.Thread(target=self.read_serial, daemon=True).start()
                return
        self.text_area.insert(tk.END, "Dispositivo CH340 não encontrado.\n")

    def read_serial(self):
        buffer = ""
        while self.running and self.serial_port and self.serial_port.is_open:
            try:
                line = self.serial_port.readline().decode(errors='ignore').strip()
                if line:
                    self.text_area.insert(tk.END, f"Recebido: {line}\n")
                    self.text_area.see(tk.END)

                    buffer += line + " "
                    self.check_combined_packets(buffer)

            except Exception as e:
                self.text_area.insert(tk.END, f"Erro ao ler: {e}\n")
                break

    def check_combined_packets(self, text):
        r_matches = re.findall(r"r:([0-9A-Fa-f]{4})", text)
        if len(r_matches) >= 2:
            # Versão: terceiro dígito do primeiro r:
            first_r = r_matches[0]
            if len(first_r) >= 3:
                version = first_r[2]
            else:
                version = "?"

            # Index: segundo r:, ignora 3 bits e pega 7 seguintes
            second_r = r_matches[1]
            bin_value = bin(int(second_r, 16))[2:].zfill(16)
            extracted_bits = bin_value[3:10]
            index_decimal = int(extracted_bits, 2)

            info = f"Versão: {version}   |   Index: {index_decimal}"
            self.info_box.config(state=tk.NORMAL)
            self.info_box.delete(1.0, tk.END)
            self.info_box.insert(tk.END, info)
            self.info_box.config(state=tk.DISABLED)

    def send_stream(self):
        if self.serial_port and self.serial_port.is_open:
            try:
                self.serial_port.write((self.stream_to_send + '\n').encode())
                self.text_area.insert(tk.END, f"Enviado: {self.stream_to_send}\n")
                self.text_area.see(tk.END)
            except Exception as e:
                self.text_area.insert(tk.END, f"Erro ao enviar: {e}\n")

    def toggle_serial(self):
        if self.serial_port:
            if self.serial_port.is_open:
                self.running = False
                self.serial_port.close()
                self.send_button.config(state=tk.DISABLED)
                self.toggle_button.config(text="Habilitar")
                self.text_area.insert(tk.END, "Porta desabilitada.\n")
            else:
                try:
                    self.serial_port.open()
                    self.running = True
                    self.send_button.config(state=tk.NORMAL)
                    self.toggle_button.config(text="Desabilitar")
                    self.text_area.insert(tk.END, "Porta habilitada.\n")
                    threading.Thread(target=self.read_serial, daemon=True).start()
                except Exception as e:
                    self.text_area.insert(tk.END, f"Erro ao habilitar: {e}\n")

    def restart_serial(self):
        if self.serial_port:
            self.running = False
            try:
                self.serial_port.close()
            except:
                pass
            self.serial_port = None
            self.send_button.config(state=tk.DISABLED)
            self.toggle_button.config(text="Desabilitar")
            self.text_area.insert(tk.END, "Reiniciando...\n")
        self.detect_and_connect()

if __name__ == "__main__":
    root = tk.Tk()
    app = SerialCH340App(root)
    root.mainloop()