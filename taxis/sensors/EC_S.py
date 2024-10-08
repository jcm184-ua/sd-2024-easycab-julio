import socket
import threading
import time

# Variable global para el estado del sensor (True = OK, False = KO)
estado = True

def manejar_socket(ec_de_ip, ec_de_port):
    """Conectar al EC_DE y enviar el estado del sensor cada segundo"""
    global estado
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((ec_de_ip, int(ec_de_port)))
        print(f"Conectado a EC_DE en {ec_de_ip}:{ec_de_port}")
        
        while True:
            mensaje = "OK" if estado else "KO"
            s.sendall(mensaje.encode('utf-8'))
            time.sleep(1)

def cambiar_estado():
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
    # Dirección IP y puerto del EC_DE (proporcionados como argumentos de línea de comandos)
    ec_de_ip = input("Ingresa la IP del EC_DE: ")
    ec_de_port = input("Ingresa el puerto del EC_DE: ")
    
    # Crear el hilo para manejar la conexión por socket con EC_DE
    hilo_socket = threading.Thread(target=manejar_socket, args=(ec_de_ip, ec_de_port))
    hilo_socket.daemon = True  # El hilo terminará cuando termine el programa principal
    hilo_socket.start()

    # Menú para cambiar el estado
    cambiar_estado()

if _name== "main_":
    main()
