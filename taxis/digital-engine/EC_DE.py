import sys
import socket
import threading

def comprobarArgumentos(argumentos):
    # print(sys.argv)
    if len(argumentos) != 8:
        print("CHECKS: ERROR EN EL NÚMERO DE ARGUMENTOS")
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
    CENTRAL_PORT = sys.argv[2]
    BROKER_IP = sys.argv[3]
    BROKER_PORT = sys.argv[4]
    SENSOR_IP = sys.argv[5]  # IP para escuchar al sensor
    SENSOR_PORT = sys.argv[6]  # Puerto para escuchar al sensor
    ID = sys.argv[7]

    # Crear un hilo con socket servidor para escuchar a un EC_S
    hilo_sensor = threading.Thread(target=manejar_sensor, args=(SENSOR_IP, SENSOR_PORT))
    hilo_sensor.start()

    # Aquí puedes continuar con el resto de la lógica de EC_DE.py, como autenticación

if _name_ == "_main_":
    main()
