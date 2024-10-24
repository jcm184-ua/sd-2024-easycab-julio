import sys
import socket
import threading
from kafka import KafkaProducer, KafkaConsumer
import time

sys.path.append('../../shared')
from EC_Shared import *
from EC_Map import Map

TOPIC_TAXIS = 'TAXIS'
MAX_CONECTED_SENSORS = 1

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

def gestionarSocketSensores():
    #print(f"INFO: Iniciando socket de escucha para sensores en {THIS_ADDR}")

    socketEscucha = abrirSocketServidor(THIS_ADDR)
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
        mensaje = recibirMensajeServidor(conexion)
        if mensaje == None:
            print(f"INFO: Conexión con el sensor {direccion} perdida.")
            modificarSensoresConectados(-1)
            break
        else:
            print(f"INFO: Mensaje del sensor {direccion} recibido: {mensaje}")
            if mensaje == "OK":
                estadoSensor = True
            elif mensaje == "KO":
                estadoSensor = False
            else:
                print(f"ERROR: MENSAJE DESCONOCIDO: {mensaje}")

def gestionarSocketCentral():
    socketCentral = abrirSocketCliente(CENTRAL_ADDR)
    print("INFO: Intentando autenticar en central")
    
    while True:
        enviarMensajeCliente(socketCentral, f"[EC_DE_{ID}->EC_Central][AUTH_REQUEST]")
        time.sleep(5)


    while True:
        mensaje = recibirMensajeCliente(conexion)
        if mensaje == None:
            print(f"INFO: Conexión con el servidor {direccion} perdida.")
            break
        else:
            print(f"INFO: Mensaje del sensor {direccion} recibido: {mensaje}")
            if mensaje == "OK":
                estadoSensor = True
            elif mensaje == "KO":
                estadoSensor = False
            else:
                print(f"ERROR: MENSAJE DESCONOCIDO: {mensaje}")

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

    # cuando reciba una solicitud de servicio moverse hacia alli con mover(origenx, origeny, destinoX, destinoY)
    # cuando tengas el mapa puedes diseñar la función moverse que vaya devolviendo los movimientos que te lleven a una posicion

if __name__ == "__main__":
    main()
