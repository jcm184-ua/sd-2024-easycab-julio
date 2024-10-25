import sys
import re
import socket
import threading
from kafka import KafkaProducer, KafkaConsumer
import time
import os

sys.path.append('../../shared')
from EC_Shared import *
from EC_Map import Map

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

posX = None
posY = None
destX = None
destY = None


def comprobarArgumentos(argumentos):
    if len(argumentos) != 7:
        #print("CHECKS: ERROR LOS ARGUMENTOS. Necesito estos argumentos: <CENTRAL_IP> <CENTRAL_PORT> <BROKER_IP> <BROKER_PORT> <SENSOR_IP> <SENSOR_PORT> <ID>")
        print("CHECKS: ERROR LOS ARGUMENTOS. Necesito estos argumentos: <CENTRAL_IP> <CENTRAL_PORT> <BROKER_IP> <BROKER_PORT> <LISTEN_PORT> <ID>")
        exit()
    printInfo("Número de argumentos correcto.")

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
    printInfo("Constantes asignadas")

def modificarSensoresConectados(valor):
    global sensoresConectados
    sensoresConectados += valor

def gestionarSocketSensores():
    socketEscucha = abrirSocketServidor(THIS_ADDR)
    socketEscucha.listen()
    # TODO: Mas sensores?

    while True:
        conexion, direccion = socketEscucha.accept()
        printInfo(f"Nueva conexión de un socket en {conexion}, {direccion}.")
        if (sensoresConectados < MAX_CONECTED_SENSORS):
            modificarSensoresConectados(+1)
            printInfo(f"Límite de sensores no alcanzado. Aceptando conexión con socket en {direccion}.")
            hiloSensor = threading.Thread(target=gestionarSensor, args=(conexion, direccion))
            hiloSensor.start()
        else:
            printInfo(f"Límite de sensores ya alcanzado. Cerrando conexión con socket en {direccion}.")
            conexion.close()

def gestionarSensor(conexion, direccion):
    global estadoSensor

    while True:
        mensaje = recibirMensajeServidorSilent(conexion)
        if mensaje == None:
            printInfo(f"Conexión con el sensor {direccion} perdida.")
            estadoSensor = False
            publicarMensajeEnTopic(f"[EC_DE_{ID}->EC_Central][ESTADO][KO]", TOPIC_TAXIS, BROKER_ADDR)
            modificarSensoresConectados(-1)
            break
        else:
            if mensaje == "OK" and estadoSensor == True:
                pass
            elif mensaje == "KO" and estadoSensor == False:
                pass
            elif mensaje != "OK" and mensaje != "KO":
                printError(f"SENSOR: MENSAJE DESCONOCIDO: {mensaje}")
            else:
                printInfo("Cambiando estado del sensor")
                estadoSensor = not estadoSensor
                if mensaje == "OK":
                    publicarMensajeEnTopic(f"[EC_DE_{ID}->EC_Central][ESTADO][OK]", TOPIC_TAXIS, BROKER_ADDR)
                elif mensaje == "KO":
                    publicarMensajeEnTopic(f"[EC_DE_{ID}->EC_Central][ESTADO][KO]", TOPIC_TAXIS, BROKER_ADDR)

def recibirMapaLogin(socket):
    try:
        # PASO DE LA RESILIENCIA DE SI SE INTERRUMPE AQUI YA QUE ES EL LOGIN
        mensaje = recibirMensajeCliente(socket)
        camposMensaje = re.findall('[^\[\]]+', mensaje)
        printInfo("Mapa recibido")
        #print(camposMensaje)
        mapa.loadJson(camposMensaje[1])
        mapa.loadActiveTaxis(camposMensaje[2])
        mapa.print()
    except Exception as e:
        printError(f"MAPA: Error al recibir el mapa: {e}")

def gestionarConexionCentral():
    global posX, posY, destX, destY

    while True:
        try:
            socket = abrirSocketCliente(CENTRAL_ADDR)
            printInfo("Intentando autenticar en central")
            enviarMensajeCliente(socket, f"[EC_DE_{ID}->EC_Central][AUTH_REQUEST]['estado_sensor']['posicion?']")
            time.sleep(5)
            while True:
                mensaje = recibirMensajeCliente(socket)
                camposMensaje = re.findall('[^\[\]]+', mensaje)
                #print(camposMensaje)
                if mensaje == None:
                    printInfo(f"Mensaje vacio. ¿Conexión con el servidor perdida.?")
                    break
                else:
                    printInfo(f"Mensaje del servidor recibido: {mensaje}")
                    if mensaje.startswith(f"[EC_Central->EC_DE_{ID}][AUTHORIZED]"):
                        try:
                            printInfo("Autentificación correcta")
                            posX = camposMensaje[2].split(",")[0]
                            posY = camposMensaje[2].split(",")[1]
                            recibirMapaLogin(socket)
                            hiloMovimientosAleatorios = threading.Thread(target=movimientosAleatorios)
                            #hiloMovimientosAleatorios.start()
                        except:
                            printError("ENGINE: Error al decodificar mensaje 1")
                    elif mensaje == f"[EC_Central->EC_DE_{ID}][NOT_AUTHORIZED]":
                        printError("ENGINE: Autentificación incorrecta. Finalizando ejecución.")
                        os._exit(1)
                        #exit()
                    else:
                        printError(f"ENGINE: MENSAJE DESCONOCIDO: {mensaje}")
        except Exception as e:
            printWarning(f"SOCKET CAIDO: {e}.")
            time.sleep(3)
            printInfo(f"Reintentando conexión...")

        #Una vez autorizados y con posición, esperar a que se nos indique un servicio

def gestionarBroker():
    global mapa

    printInfo(f"Conectando al broker en la dirección ({BROKER_ADDR}) como consumidor.")
    consumidor = conectarBrokerConsumidor(BROKER_ADDR, TOPIC_TAXIS)
    for mensaje in consumidor:
        camposMensaje = re.findall('[^\[\]]+', mensaje.value.decode(FORMAT))
        #print(camposMensaje)
        if camposMensaje[0] == ("EC_Central->ALL"):
            mapa.loadJson(camposMensaje[1])
            mapa.loadActiveTaxis(camposMensaje[2])
            mapa.print()
        else:
            # TODO: Informar mas que decir que error
            pass
            printInfo(f"Mensaje desconocido descartado: {mensaje}")

def mover(x, y):
    if (x > 20) or (x < 0) or (y > 20) or (y < 0):
        print("ERROR: Movimiento demasiado grande")
    else:
        print(f"INFO: Moviendo a dirección ({x},{y})")
        publicarMensajeEnTopic(f"[EC_DE_{ID}->EC_Central][MOVIMIENTO][{x},{y}]", TOPIC_TAXIS, BROKER_ADDR)

def calcularMovimientos():
    global posX, posY, destX, destY

    while True:
        if estadoSensor:
            if destX != None or destY != None:
                if posX != destX or posY != destY:        
                    delta_x = int(destX) - int(posX)
                    delta_y = int(destY) - int(posY)

                    step_x = 1 if delta_x > 0 else -1 if delta_x < 0 else 0
                    step_y = 1 if delta_y > 0 else -1 if delta_y < 0 else 0

                    print(f"Me muevo de {posX},{posY} a {destX},{destY} en dirección ({step_x},{step_y})")

                    posX = int(posX) + step_x
                    posY = int(posY) + step_y

                    mover(posX, posY)

            #print(datetime.now(), "INFO: Movimiento aleatorio", threading.get_ident())
            #mover(1, 1)
        time.sleep(1)


def main():
    comprobarArgumentos(sys.argv)
    asignarConstantes(sys.argv)

    threading.Thread(target=calcularMovimientos).start()

    hiloSocketSensores = threading.Thread(target=gestionarSocketSensores)
    hiloSocketSensores.start()

    hiloSocketCentral = threading.Thread(target=gestionarConexionCentral)
    hiloSocketCentral.start()

    hiloBroker = threading.Thread(target=gestionarBroker)
    hiloBroker.start()

    # cuando reciba una solicitud de servicio moverse hacia alli con mover(origenx, origeny, destinoX, destinoY)
    # cuando tengas el mapa puedes diseñar la función moverse que vaya devolviendo los movimientos que te lleven a una posicion

if __name__ == "__main__":
    main()
