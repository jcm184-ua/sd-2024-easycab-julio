import sys
import socket
import threading

def comprobarArgumentos(argumentos):
    if len(argumentos) != 8:
        print("CHECKS: ERROR LOS ARGUMENTOS. Necesito estos argumentos: <CENTRAL_IP> <CENTRAL_PORT> <BROKER_IP> <BROKER_PORT> <SENSOR_IP> <SENSOR_PORT> <ID>")
        exit()
    print("INFO: Número de argumentos correcto.")

def manejar_sensor(sensor_ip, sensor_port):
    """Abrir socket servidor para recibir mensajes del EC_S (sensor)"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((sensor_ip, int(sensor_port)))
        s.listen(1)  # Limitar a un máximo de un sensor
        print(f"Esperando conexión del sensor en {sensor_ip}:{sensor_port}...")

        conn, addr = s.accept()
        with conn:
            print(f"Conexión establecida con el sensor en {addr}")
            while True:
                data = conn.recv(1024)
                if not data:
                    break

def main():
    comprobarArgumentos(sys.argv)

    # Asignamos las constantes
    CENTRAL_IP = sys.argv[1]
    CENTRAL_PORT = int(sys.argv[2])
    BROKER_IP = sys.argv[3]
    BROKER_PORT = int(sys.argv[4])
    SENSOR_IP = sys.argv[5]  # IP para escuchar al sensor (Innecesario?)
    SENSOR_PORT = int(sys.argv[6])  # Puerto para escuchar al sensor
    ID = sys.argv[7]

    # Abrir un hilo con socket servidor para escuchar a un EC_S
    hilo_sensor = threading.Thread(target=manejar_sensor, args=(SENSOR_IP, SENSOR_PORT))
    hilo_sensor.start()
    # esperar hasta que conecte un sensor para proseguir. Limitar a un máximo de un sensor

    # Abrir un hili socket cliente a main para autenticarse.
    ADDR_CENTRAL = (CENTRAL_IP, CENTRAL_PORT)

    # Aqui central verificará que su id existe en la base de datos y que está desconectado
    #                                               (garantizar que dos taxis no tienen mismo id)
    # socket / autenticarse()
    # una vez conectado el engine le dará la posición (por defecto x=1, y=1)

    # Permanecer a la espera de lo que se publica en el topic MOVIMIENTOS_TAXIS
    # Actualizar el mapa con topic MAPA

    # cuando reciba una solicitud de servicio moverse hacia alli con mover(origenx, origeny, destinoX, destinoY)
    # cuando tengas el mapa puedes diseñar la función moverse que vaya devolviendo los movimientos que te lleven a una posicion


if __name__ == "__main__":
    main()
