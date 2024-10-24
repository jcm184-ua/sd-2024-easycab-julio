import sys
import socket
import threading
from kafka import KafkaProducer, KafkaConsumer
import time

sys.path.append('../../shared')
from EC_Map import Map

HEADER = 64
FORMAT = 'utf-8'

CENTRAL_IP = None
CENTRAL_PORT = None
CENTRAL_ADDR = None
BROKER_IP = None
BROKER_PORT = None
BROKER_ADDR = None
HOST = "" # Simbólico, nos permite escuchar en todas las interfaces de red
LISTEN_PORT = None
THIS_ADDR = None
ID = None
MAX_CONECTED_SENSORS = 1
TOPIC_TAXIS = 'TAXIS'

sensoresConectados = 0
estadoSensores = [] #Si tengo varios sensores comprobar todos los sensores.
estadoSensor = False
mapa = Map()

def comprobarArgumentos(argumentos):
    if len(argumentos) != 7:
        #print("CHECKS: ERROR LOS ARGUMENTOS. Necesito estos argumentos: <CENTRAL_IP> <CENTRAL_PORT> <BROKER_IP> <BROKER_PORT> <SENSOR_IP> <SENSOR_PORT> <ID>")
        print("CHECKS: ERROR LOS ARGUMENTOS. Necesito estos argumentos: <CENTRAL_IP> <CENTRAL_PORT> <BROKER_IP> <BROKER_PORT> <LISTEN_PORT> <ID>")
        exit()
    print("INFO: Número de argumentos correcto.")

def asignarConstantes(argumentos):
    # Asignamos las constantes
    global CENTRAL_IP
    CENTRAL_IP = argumentos[1]
    global CENTRAL_PORT
    CENTRAL_PORT = int(argumentos[2])
    global CENTRAL_ADDR
    CENTRAL_ADDR =  (CENTRAL_IP, CENTRAL_PORT)
    global BROKER_IP
    BROKER_IP = argumentos[3]
    global BROKER_PORT
    BROKER_PORT = int(argumentos[4])
    global BROKER_ADDR
    BROKER_ADDR = BROKER_IP+":"+str(BROKER_PORT)
    global LISTEN_PORT
    LISTEN_PORT = int(argumentos[5])
    global THIS_ADDR
    THIS_ADDR = (HOST, LISTEN_PORT)
    global ID
    ID = int(argumentos[6])
    print("INFO: Constantes asignadas")

def modificarSensoresConectados(valor):
    global sensoresConectados
    sensoresConectados += valor

def abrirSocketEscucha():
    print(f"INFO: Abriendo socket de escucha en la dirección {THIS_ADDR}.")
    socketAbierto = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    socketAbierto.bind(THIS_ADDR)
    return socketAbierto

def abrirSocketCentral():
    print(f"INFO: Abriendo socket a central en la dirección {THIS_ADDR}.")
    socketCentral = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    socketCentral.connect(CENTRAL_ADDR)
    return socketCentral

def gestionarSocketSensores():
    #print(f"INFO: Iniciando socket de escucha para sensores en {THIS_ADDR}")

    socketEscucha = abrirSocketEscucha()
    socketEscucha.listen()

    # TODO: Mas sensores?

    while True:
        conexion, direccion = socketEscucha.accept()
        print(f"INFO: Nueva conexión de un socket en {conexion}, {direccion}.")
        if (sensoresConectados < MAX_CONECTED_SENSORS):
            modificarSensoresConectados(+1)
            print(f"INFO: Límite de sensores no alcanzado. Aceptando conexión con socket en {direccion}.")
            hiloSensor = threading.Thread(target=gestionarSensor, args=(conexion, direccion))
            hiloSensor.start()
        else:
            print(f"INFO: Límite de sensores ya alcanzado. Cerrando conexión con socket en {direccion}.")
            conexion.close()

def gestionarSensor(conexion, direccion):
    global estadoSensor

    while True:
        msg_length = conexion.recv(HEADER).decode(FORMAT)
        if msg_length:
            msg_length = int(msg_length)
            msg = conexion.recv(msg_length).decode(FORMAT)
            print(f"INFO: Mensaje del sensor {direccion} recibido: {msg}")
            if msg == "OK":
                estadoSensor = True
            elif msg == "KO":
                estadoSensor = False
            else:
                print("ERROR: Mensaje desconocido")
        else:
            # El socket se ha desconectado
            print(f"INFO: Conexión con el sensor {direccion} perdida.")
            modificarSensoresConectados(-1)
            break

def enviarMensajeSobreSocket(socket, mensaje):
    mensaje_codificado = mensaje.encode(FORMAT)
    longitud_mensaje = len(mensaje_codificado)
    longitud_envio = str(longitud_mensaje).encode(FORMAT)
    longitud_envio += b' ' * (HEADER - len(longitud_envio))
    socket.send(longitud_envio)
    socket.send(mensaje_codificado)
    print(f'INFO: Mensaje "{mensaje}" enviado a través de socket {socket.getsockname()}.')

def gestionarSocketCentral():
    socketCentral = abrirSocketCentral()
    print("INFO: Intentando autenticar en central")
    
    while True:
        enviarMensajeSobreSocket(socketCentral, f"[EC_DE_{ID}->EC_Central][AUTH_REQUEST]")
        time.sleep(5)

    while True:
        msg_length = conexion.recv(HEADER).decode(FORMAT)
        if msg_length:
            msg_length = int(msg_length)
            msg = conexion.recv(msg_length).decode(FORMAT)
            print(f"INFO: Mensaje del sensor {direccion} recibido: {msg}")
            if msg == "OK":
                estadoSensor = True
            elif msg == "KO":
                estadoSensor = False
            else:
                print("ERROR: Mensaje desconocido")
        else:
            # El socket se ha desconectado
            print(f"INFO: Conexión con el sensor {direccion} perdida.")
            modificarSensoresConectados(-1)
            break


def publicarMensaje(mensaje, topic):
    print(f"INFO: Conectando al broker en la dirección ({BROKER_ADDR}) como productor.")
    conexion = KafkaProducer(bootstrap_servers=BROKER_ADDR)
    conexion.send(topic,(mensaje.encode(FORMAT)))
    print(f"INFO: Mensaje {mensaje} publicado.")

def gestionarBroker():
    print(f"INFO: Conectando al broker en la dirección ({BROKER_ADDR}) como consumidor.")
    conexion = KafkaConsumer(TOPIC_TAXIS, bootstrap_servers=BROKER_ADDR)
    for mensaje in conexion:
        if mensaje.value.decode(FORMAT).startswith(f"[EC_Central->All]"):
            continue
            print(f"INFO: Mensaje recibido: {mensaje}")
            global mapa
            mapa.loadJson(mensaje)
            mapa.print()
        else:
            # TODO: Informar mas que decir que error
            print(f"INFO: Mensaje desconocido descartado: {mensaje}")

def mover(x, y):
    if (x > 1) or (x < -1) or (y > 1) or (y < -1):
        print("ERROR: Movimiento demasiado grande")
    else:
        print(f"INFO: Moviendo en dirección ({x},{y})")
        publicarMensaje(f"[EC_DigitalEngine_{ID}->EC_Central][({x},{y})]", TOPIC_TAXIS)

def movimientosAleatorios():
    while True:
        if estadoSensor:
            print("INFO: Movimiento aleatorio")
            mover(1, 1)
        time.sleep(2)

def main():
    comprobarArgumentos(sys.argv)
    asignarConstantes(sys.argv)

    hiloSocketSensores = threading.Thread(target=gestionarSocketSensores)
    hiloSocketSensores.start()

    hiloSocketCentral = threading.Thread(target=gestionarSocketCentral)
    hiloSocketCentral.start()

    hiloBroker = threading.Thread(target=gestionarBroker)
    hiloBroker.start()

    hiloMovimientosAleatorios = threading.Thread(target=movimientosAleatorios)
    hiloMovimientosAleatorios.start()




    #hilo_sensor = threading.Thread(target=gestionarSensor)
    #hilo_sensor.start()
    # esperar hasta que conecte un sensor para proseguir. Limitar a un máximo de un sensor

    # Abrir un hili socket cliente a main para autenticarse.


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
