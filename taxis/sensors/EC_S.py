import sys
import socket
import threading
import time

sys.path.append('../../shared')
from EC_Shared import *

TAXI_IP = None
TAXI_PORT = None
TAXI_ADDR = None

# Variable global para el estado del sensor (True = OK, False = KO)
estadoSensor = True

def comprobarArgumentos(argumentos):
    if len(argumentos) != 3:
        printError("Necesito estos argumentos: <TAXI_IP> <TAXI_PORT>")
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
                mensaje = "OK" if estadoSensor else "KO"
                enviarMensajeCliente(socket, mensaje)
                enviarMensajeCliente(socket, f"[EC_Sensor->EC_DE_?][{mensaje}]")
                time.sleep(1)
                printMenu()

        except BrokenPipeError as error:
            printWarning("Se ha perdido la conexión con el EC_DE.")
        except ConnectionRefusedError as error:
            printWarning("No se ha podido conectar con el EC_DE.")
        finally:
            time.sleep(3)
            printInfo(f"Reintentando conexión...")
            printMenu()

def printMenu():
    if estadoSensor:
        print("\nPresione [Enter] para generar una incidencia...\n")
    else:
        print("\nPresione [Enter] para finalizar la incidencia...\n")

def gestionarCambioEstado():
    global estadoSensor
    while True:
        input("")
        #printDebug("Detectada pulsacion")
        estadoSensor = not estadoSensor

def main():
    comprobarArgumentos(sys.argv)
    asignarConstantes(sys.argv)

    hilo_socket = threading.Thread(target=gestionarConexionTaxi)
    hilo_socket.start()

    hilo_estado = threading.Thread(target=gestionarCambioEstado)
    hilo_estado.start()

if __name__ == "__main__":
    main()
