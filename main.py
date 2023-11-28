import sys
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
import os
import serial
import serial.tools.list_ports
from Tinyprog.__init__ import TinyProg
import sys
import logging
import subprocess
import glob
import shutil
from time import sleep
import recursos

directorio = None


class StdoutRedirector:
    def __init__(self, text_widget):
        self.text_widget = text_widget

    def write(self, str):
        self.text_widget.insert(tk.END, str)
        self.text_widget.see(tk.END)  # Desplaza automáticamente hacia la última línea
        self.text_widget.update()  # Forzar una actualización de la ventana

    def flush(self):
        pass  # Dejar flush vacío, ya que no es necesario

def redirigir_output(text_widget):
    sys.stdout = StdoutRedirector(text_widget)


#ser = SerialPort("COM5")

"""
def seleccionar_puerto():
    seleccion = combo.get()
    etiqueta.config(text=f"Puerto seleccionado: {seleccion}")
"""

# Refresca los puertos COM del PC
def refrescar_puertos():
    puertos_serie = [port.device for port in serial.tools.list_ports.comports()]
    combo['values'] = puertos_serie
    if len(puertos_serie) > 0:
        combo.set(puertos_serie[0])
    else:
        combo.set("")

    logging.info("Puertos disponibles refrescados\n")

def strict_query_user(question):
    valid = {"yes": True}

    prompt = " [yes/NO] > "

    while True:
        sys.stdout.write(question + prompt)
        choice = input().lower()
        return valid.get(choice, False)

def check_if_overwrite_bootloader(addr, length, userdata_range):
    ustart = userdata_range[0]
    uend = userdata_range[1]

    if addr < ustart or addr + length >= uend:
        print("")
        print("    !!! WARNING !!!")
        print("")
        print("    The address given may overwrite the USB bootloader. Without the")
        print("    USB bootloader the board will no longer be able to be programmed")
        print("    over the USB interface. Without the USB bootloader, the board can")
        print("    only be programmed via the SPI flash interface on the bottom of")
        print("    the board")
        print("")
        retval = strict_query_user("    Are you sure you want to continue? Type in 'yes' to overwrite bootloader.")
        print("")
        return retval

    return True



def procesar_archivo():

    files = glob.glob(directorio + '/*.v')
    if len(files) > 0:
        subprocess.Popen("apio verify", cwd=directorio)
        sleep(2)
        subprocess.Popen("apio build", cwd=directorio)
        sleep(2)
        archivo = directorio + "/hardware.bin"
        if os.path.exists(archivo):
            # Realiza la acción que desees con el archivo binario seleccionado
            # Por ejemplo, puedes imprimir la ruta del archivo
            print("Archivo seleccionado:", archivo)

            #ser = SerialPort('COM5')
            puerto = combo.get()
            ser=serial.Serial(puerto, timeout=1.0, writeTimeout=1.0).__enter__()

            tinyprog = TinyProg(ser)
            bitstream = tinyprog.slurp(archivo)
            addr = tinyprog.meta.userimage_addr_range()[0]
            print("    Programming at addr 0x{:06x}".format(addr))
            if not tinyprog.program_bitstream(addr, bitstream):
                print("Failed to program... exiting")
                text_widget.insert(tk.END, "\nFallo al programar\n")
                #sys.exit(1)
            else:
                tinyprog.boot()
                text_widget.insert(tk.END, "\nProgramado correctamente\n")
                #sys.exit(0)
        else:
            print("No existen *.v en el directorio")

# Seleccion de directorio, crea .init y .pcf
def sel_folder():
    global directorio
    directorio = filedialog.askdirectory()
    subprocess.Popen("apio init --board TinyFPGA-BX -y", cwd=directorio)
    #shutil.copyfile('./Resources/pins.pcf', directorio + '/pins.pcf')
    with open(directorio + "/pins.pcf", 'w') as f:
        f.write(recursos.pins_pcf)

# Comprueba si existe *.v  lanza apio verify
def verify():
    text_widget.delete('1.0',tk.END)
    files = glob.glob(directorio + '/*.v')
    if len(files) > 0:
        subprocess.Popen("apio verify", cwd=directorio)
        sleep(2)
    else:
        print("No existen *.v en el directorio")
        print("Crea tu archivo verilog")


def build():
    files = glob.glob(directorio + '/*.v')
    if len(files) > 0:
        p=subprocess.Popen("apio build", cwd=directorio)
        p.wait()
        sleep(2)
        archivo = directorio + "/hardware.bin"
        if os.path.exists(archivo):
            # Realiza la acción que desees con el archivo binario seleccionado
            # Por ejemplo, puedes imprimir la ruta del archivo
            print("Archivo seleccionado:", archivo)

            # ser = SerialPort('COM5')
            puerto = combo.get()
            ser = serial.Serial(puerto, timeout=1.0, writeTimeout=1.0).__enter__()

            tinyprog = TinyProg(ser)
            bitstream = tinyprog.slurp(archivo)
            addr = tinyprog.meta.userimage_addr_range()[0]
            print("    Programming at addr 0x{:06x}".format(addr))
            if not tinyprog.program_bitstream(addr, bitstream):
                print("Failed to program... exiting")
                text_widget.insert(tk.END, "\nFallo al programar\n")
                # sys.exit(1)
            else:
                tinyprog.boot()
                text_widget.insert(tk.END, "\nProgramado correctamente\n")
                # sys.exit(0)



ventana = tk.Tk()
ventana.title("Program Loader")
# Configura el tamaño de la ventana
ventana.geometry("400x400")  # Ancho x Alto en píxeles
# Obtener la lista de puertos serie disponibles
puertos_serie = [port.device for port in serial.tools.list_ports.comports()]

# Crear una variable para almacenar la selección
combo = ttk.Combobox(ventana, values=puertos_serie)
combo.pack(pady=10)

# Botón para mostrar la selección
btn_recargar = tk.Button(ventana, text="Recargar", command=refrescar_puertos)
btn_recargar.pack()

etiqueta = tk.Label(ventana, text="")
etiqueta.pack(pady=10)

#Botón Seleccionar Carpeta
btn_folder = tk.Button(ventana, text="Seleccionar carpeta", command=sel_folder)
btn_folder.pack()

#Boton Verificar
btn_verify = tk.Button(ventana, text="Verificar",command=verify)
btn_verify.pack()

#Boton Build & Upload
btn_build = tk.Button(ventana, text="Build & Upload",command=build)
btn_build.pack()


text_widget = tk.Text(ventana, wrap=tk.WORD)
text_widget.pack()

redirigir_output(text_widget)
refrescar_puertos()



ventana.mainloop()

