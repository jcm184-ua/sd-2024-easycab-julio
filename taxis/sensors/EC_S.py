import sys
import socket
import threading
import time

sys.path.append('../../shared')
from EC_Shared import *

# Variable global para el estado del sensor (True = OK, False = KO)
estado = True

TAXI_IP = None
TAXI_PORT = None
TAXI_ADDR = None

def comprobarArgumentos(argumentos):
    if len(argumentos) != 3:
        printInfo("ERROR LOS ARGUMENTOS. Necesito estos argumentos: <TAXI_IP> <TAXI_PORT>")
        exit()
    printInfo(f"Número de argumentos correcto.")

def asignarConstantes(argumentos):
    global TAXI_IP
    TAXI_IP = argumentos[1]
    global TAXI_PORT
    TAXI_PORT = int(argumentos[2])
    global TAXI_ADDR
    TAXI_ADDR =  (TAXI_IP, TAXI_PORT)
    printInfo(f"Constantes asignadas.")

def gestionarConexionTaxi():
    global estadoSensor

    while True:
        try:
            socket = abrirSocketCliente(TAXI_ADDR)
            while True:
                # MEJORAR MENSAJE [EC_Sensor->EC_DE_?][OK]
                printInfo(f"Enviando estado del sensor: {estadoSensor}")
                enviarMensajeCliente(socket, estadoSensor)
                time.sleep(1)

        except Exception as e:
            printInfo(f"WARNING: SOCKET CAIDO: {e}.")
            time.sleep(3)
            printInfo(f"INFO: Reintentando conexión...")

#TODO: PONER EL DE PEDRE
def cambiar_estado():
    global estadoSensor
    while True:
        if estadoSensor == "OK":
            input("Presiona Enter para generar una incidencia (KO)...\n")
            estadoSensor = "KO"
        else:
            input("Presiona Enter para arreglar una incidencia (KO)...\n")
            estadoSensor = "OK"

def main():
    comprobarArgumentos(sys.argv)
    asignarConstantes(sys.argv)

    hilo_socket = threading.Thread(target=gestionarConexionTaxi)
    hilo_socket.start()

    cambiar_estado()

if __name__ == "__main__":
    main()
