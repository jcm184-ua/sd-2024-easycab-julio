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
        print("CHECKS: ERROR LOS ARGUMENTOS. Necesito estos argumentos: <TAXI_IP> <TAXI_PORT>")
        exit()
    print("INFO: Número de argumentos correcto.")

def asignarConstantes(argumentos):
    global TAXI_IP
    TAXI_IP = argumentos[1]
    global TAXI_PORT
    TAXI_PORT = int(argumentos[2])
    global TAXI_ADDR
    TAXI_ADDR =  (TAXI_IP, TAXI_PORT)
    print("INFO: Constantes asignadas.")

def gestionarConexionTaxi():
    global estado

    while True:
        try:
            socket abrirSocketCliente(TAXI_ADDR)

        except Exception as e:
            print(f"WARNING: SOCKET CAIDO: {e}.")
            time.sleep(3)
            print(f"INFO: Reintentando conexión...")
    
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((TAXI_IP, int(TAXI_PORT)))
            print(f"Conectado a EC_DE en {TAXI_IP}:{TAXI_PORT}")
            
            # MEJORAR MENSAJE [EC_Sensor->EC_DE_?][OK]
            while True:
                mensaje = "OK" if estado else "KO"
                message = mensaje.encode(FORMAT)
                msg_length = len(message)
                send_length = str(msg_length).encode(FORMAT)
                send_length += b' ' * (HEADER - len(send_length))
                s.send(send_length)
                s.send(message)
                #s.sendall(mensaje.encode('utf-8'))
                time.sleep(1)
    except Exception as e:
        print(f"SOCKET CAIDO {e}")

def cambiar_estado():
    # haz un pequeño programa que con un hilo conecte con socket a un EC_DE, que tenga una bool global estado
    # y que en otro hilo cuando pulses una tecla (o con un menu) cambie de estado.  
    # El hilo del socket cada segundo comprobará la variable global y le envie el estado al taxi
    """Función para cambiar el estado del sensor"""
    global estado
    while True:
        opcion = input("\nMenú:\n1. Cambiar estado\n2. Salir\nSelecciona una opción: ")
        if opcion == "1":
            estado = not estado
            estado_str = "OK" if estado else "KO"
            print(f"Estado cambiado a: {estado_str}")
        elif opcion == "2":
            print("Saliendo...")
            break
        else:
            print("Opción inválida, intenta de nuevo.")
        time.sleep(1)  # Pequeño retardo para evitar spam en el menú

def main():
    comprobarArgumentos(sys.argv)
    asignarConstantes(sys.argv)

    hilo_socket = threading.Thread(target=gestionarConexionTaxi)
    hilo_socket.start()

    #TODO: Hacer bien y en ventana extra
    cambiar_estado()

if __name__ == "__main__":
    main()
