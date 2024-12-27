import sys
import re
import socket, ssl
import threading
import json
from kafka import KafkaProducer, KafkaConsumer
import time
import os
from resources.privateKey import BROKER_KEY
from cryptography.fernet import Fernet

import requests

sys.path.append('../../shared')
from EC_Shared import *
from EC_Map import Map

MAX_CONECTED_SENSORS = 5

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
REGISTRY_IP = None
REGISTRY_PORT = None
API_URL = None

SERV_CERTIFICATE  = './resources/certServ.pem'
hostname = 'localhost'
context = ssl._create_unverified_context()

sensoresConectados = 0
sensoresOk = 0
estadoSensores = False
mapa = Map()

token = None
tokenCentral = None

posX = None
posY = None
cltX = None
cltY = None
destX = None
destY = None

clienteARecoger = None
clienteRecogido = False
idLocalizacion = None
irBase = False

def comprobarArgumentos(argumentos):
    if len(argumentos) != 9:
        #print("CHECKS: ERROR LOS ARGUMENTOS. Necesito estos argumentos: <CENTRAL_IP> <CENTRAL_PORT> <BROKER_IP> <BROKER_PORT> <SENSOR_IP> <SENSOR_PORT> <ID>")
        exitFatal("Necesito estos argumentos: <CENTRAL_IP> <CENTRAL_PORT> <BROKER_IP> <BROKER_PORT> <LISTEN_PORT> <ID> <REGISTRY_IP> <REGISTRY_PORT>")
    printInfo("Número de argumentos correcto.")

def asignarConstantes(argumentos):
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
    global REGISTRY_IP
    REGISTRY_IP = argumentos[7]
    global REGISTRY_PORT
    REGISTRY_PORT = int(argumentos[8])
    global API_URL
    API_URL = f"https://{REGISTRY_IP}:{REGISTRY_PORT}"
    printInfo("Constantes asignadas.")

def gestionarEstado():
    global estadoSensores

    while True:
        if estadoSensores == True and (sensoresOk != sensoresConectados or sensoresConectados < 1):
            estadoSensores = False
            publicarMensajeEnTopic(f"[EC_DE_{ID}->EC_Central][{token}][SENSORES][KO]", TOPIC_TAXIS, BROKER_ADDR, BROKER_KEY)
        elif estadoSensores == False and sensoresConectados > 0 and sensoresOk == sensoresConectados:
            estadoSensores = True
            publicarMensajeEnTopic(f"[EC_DE_{ID}->EC_Central][{token}][SENSORES][OK]", TOPIC_TAXIS, BROKER_ADDR, BROKER_KEY)
        #printDebug("Iteración de gestionarEstado()")
        #printDebug(f"estadoSensores = {estadoSensores}, sensoresConectados = {sensoresConectados}, sensoresOk = {sensoresOk}")
        time.sleep(0.2)

def gestionarSocketSensores():
    global sensoresConectados

    socketEscucha = abrirSocketServidor(THIS_ADDR)
    socketEscucha.listen()

    while True:
        conexion, direccion = socketEscucha.accept()
        printInfo(f"Nueva conexión de un sensor en {direccion}.")
        if (sensoresConectados < MAX_CONECTED_SENSORS):
            sensoresConectados += 1
            printInfo(f"Límite de sensores no alcanzado. Aceptando conexión con socket en {direccion}.")
            hiloSensor = threading.Thread(target=gestionarSensor, args=(conexion, direccion))
            hiloSensor.start()
        else:
            printInfo(f"Límite de sensores ya alcanzado. Cerrando conexión con socket en {direccion}.")
            conexion.close()

def gestionarSensor(conexion, direccion):
    global sensoresConectados, sensoresOk
    estadoSensor = False

    while True:
        try:
            mensaje = recibirMensajeServidorSilent(conexion)
            if mensaje == None:
                printWarning(f"Conexión con el sensor en {direccion} perdida.")
                sensoresOk -= 1
                sensoresConectados -= 1
                break
            else:
                #[EC_Sensor->EC_DE_?][OK]
                camposMensaje = re.findall('[^\[\]]+', mensaje)
                if camposMensaje[0] == "EC_Sensor->EC_DE_?":
                    if camposMensaje[1] == "OK" and estadoSensor == True:
                        pass
                    elif camposMensaje[1] == "KO" and estadoSensor == False:
                        pass
                    elif camposMensaje[1] != "OK" and camposMensaje[1] != "KO":
                        printError(f"Mensaje desconocido en sensor: {mensaje}")
                    else:
                        printInfo(f"Cambiando estado del sensor en {direccion} a {camposMensaje[1]}.")
                        estadoSensor = not estadoSensor
                        if camposMensaje[1] == "OK":
                            sensoresOk += 1
                        elif camposMensaje[1] == "KO":
                            sensoresOk -= 1
        except Exception as e:
            printError(f"Excepción {type(e)} en gestionarSensor().")

def recibirTokensMapaLogin(socket):
    try:
        mensaje = recibirMensajeClienteSilent(socket)
        camposMensaje = re.findall('[^\[\]]+', mensaje)
        printInfo(f"Token:'{token}', Central:'{tokenCentral}' y mapa recibidos:")
        mapa.loadJson(camposMensaje[2])
        mapa.loadActiveTaxis(camposMensaje[3])
        mapa.print()
        return True
    except Exception as e:
        printError(f"Excepción {type(e)} al recibir los tokens y el mapa: {e}.")
        return False

def gestionarConexionCentral():
    global token, tokenCentral, posX, posY, cltX, cltY, destX, destY, clienteARecoger

    while True:
        try:
            socket = abrirSocketCliente(CENTRAL_ADDR)
            socketSeguro = context.wrap_socket(socket, server_hostname=hostname)
            print(socketSeguro.version())

            printInfo("Intentando autenticar en central.")
            if estadoSensores:
                enviarMensajeCliente(socketSeguro, f"[EC_DE_{ID}->EC_Central][AUTH_REQUEST][OK][{posX},{posY}][{clienteARecoger}][{clienteRecogido}]")
            else:
                enviarMensajeCliente(socketSeguro, f"[EC_DE_{ID}->EC_Central][AUTH_REQUEST][KO][{posX},{posY}][{clienteARecoger}][{clienteRecogido}]")

            #TODO: ¿Alguna mejor forma de esperar a que central responda?
            time.sleep(0.2)

            while True:
                mensaje = recibirMensajeCliente(socketSeguro)
                if mensaje == None:
                    printWarning(f"Se ha perdido la conexión con EC_Central.")
                    break
                else:
                    camposMensaje = re.findall('[^\[\]]+', mensaje)
                    if mensaje.startswith(f"[EC_Central->EC_DE_{ID}][AUTHORIZED]"):
                        token = camposMensaje[2]
                        tokenCentral = camposMensaje[3]
                        printInfo("Autentificación correcta.")
                        posX = camposMensaje[4].split(",")[0]
                        posY = camposMensaje[4].split(",")[1]

                        if not recibirTokensMapaLogin(socketSeguro):
                            break # Se ha perdido conexión con el sensor durante el envío del mapas
                        hiloMovimientos = threading.Thread(target=manejarMovimientos)
                        hiloMovimientos.start()

                        if camposMensaje[5] != "None":
                            clienteARecoger = camposMensaje[5]
                            cltX, cltY = obtenerPosicion(camposMensaje[5], True)

                        if camposMensaje[6] != "None":
                            destX, destY = obtenerPosicion(camposMensaje[6], False)

                    elif mensaje == f"[EC_Central->EC_DE_{ID}][NOT_AUTHORIZED]":
                        socketSeguro.close()
                        printWarning("Autentificación incorrecta.")
                        break
                    else:
                        printError(f"ENGINE: MENSAJE DESCONOCIDO: {mensaje}")
        except BrokenPipeError as error:
            printWarning("Se ha perdido la conexión con EC_Central.")
        except ConnectionRefusedError as error:
            printWarning("No se ha podido conectar con EC_Central.")
        except ConnectionResetError as error:
            printError("Algo ha ocurrido en EC_Central.")
        except Exception as e:
            printWarning(f"Excepción {type(e)} inesperada en gestionarConexionCentral(): {e}")
            break
        finally:
            time.sleep(3)

        #Una vez autorizados y con posición, esperar a que se nos indique un servicio

def gestionarBroker():
    global mapa, cltX, cltY, destX, destY, clienteARecoger, idLocalizacion, irBase, clienteRecogido
    fernet = Fernet(BROKER_KEY)

    printInfo(f"Conectando al broker en la dirección ({BROKER_ADDR}) como consumidor.")
    consumidor = conectarBrokerConsumidor(BROKER_ADDR, TOPIC_TAXIS)
    while True:
        for mensaje in consumidor:

            printDebug(f"Mensaje recibido: {(fernet.decrypt(mensaje.value)).decode(FORMAT)}")
            camposMensaje = re.findall('[^\[\]]+', (fernet.decrypt(mensaje.value)).decode(FORMAT))
            #print(camposMensaje)
            if camposMensaje[0] == (f"EC_DE_{ID}->EC_Central"):
                pass
            if camposMensaje[0].startswith("EC_Central") and (camposMensaje[1] != tokenCentral):
                printInfo("Mensaje enviado por central con token incorrecto. Ignorando...")
                printDebug(camposMensaje)
                pass
            elif camposMensaje[0] == ("EC_Central->ALL"):
                    mapa.loadJson(camposMensaje[2])
                    mapa.loadActiveTaxis(camposMensaje[3])
                    mapa.print()
            elif camposMensaje[0] == f"EC_Central->BASE":
                if camposMensaje[2] == "ALL" or camposMensaje[2] == str(ID):
                    if camposMensaje[3] == "SI":
                        irBase = True
                    elif camposMensaje[3] == "NO":
                        irBase = False
            elif camposMensaje[0] == f"EC_Central->EC_DE_{ID}":
                if camposMensaje[2] == "SERVICIO":
                    printInfo(f"Me han asignado el servicio {camposMensaje[3]}")
                    clienteARecoger = camposMensaje[3].split("->")[0]
                    idLocalizacion = camposMensaje[3].split("->")[1]
                    cltX, cltY = obtenerPosicion(clienteARecoger, True)
                    destX, destY = obtenerPosicion(idLocalizacion, False)
            else:
                # TODO: Informar mas que decir que error
                pass
                #printDebug(f"Mensaje formato desconocido descartado: {(fernet.decrypt(mensaje.value)).decode(FORMAT)}.")


# ID del servicio a obtener id
# cliente = True buscamos pos cliente
# cliente = False buscamos pos localizacion

def obtenerPosicion(id, cliente):
    x, y = None, None
    if (cliente):
        posicion = mapa.getPosition(f"cliente_{id}")
    else:
        posicion = mapa.getPosition(f"localizacion_{id}")

    if posicion is not None:
        x, y = posicion.split(",")
        return x, y


import time

def mover(x, y):
    try:

        global posX, posY, clienteRecogido, clienteARecoger, idLocalizacion

        if (x > 20) or (x < 0) or (y > 20) or (y < 0):
            printError("Movimiento demasiado grande")
        elif (x == posX) and (y == posY):
            pass
        elif not estadoSensores:
            pass
            #printInfo("Sensores no operativos. No se puede realizar el movimiento")
        else:
            posX = x
            posY = y

            printInfo(f"Moviendo a dirección ({x},{y})")
            """publicarMensajeEnTopic(f"[EC_DE_{ID}->EC_Central][{token}][MOVIMIENTO][{x},{y}][{clienteARecoger}]", TOPIC_TAXIS, BROKER_ADDR, BROKER_KEY)"""

            if clienteRecogido:
                publicarMensajeEnTopic(f"[EC_DE_{ID}->EC_Central][{token}][MOVIMIENTO][{x},{y}][{clienteARecoger}][{idLocalizacion}]", TOPIC_TAXIS, BROKER_ADDR, BROKER_KEY)
            else:
                publicarMensajeEnTopic(f"[EC_DE_{ID}->EC_Central][{token}][MOVIMIENTO][{x},{y}][{None}][{None}]", TOPIC_TAXIS, BROKER_ADDR, BROKER_KEY)

    except Exception as e:
        printError(f"Excepción {type(e)} inesperada en mover(): {e}. Donde las variables globales son posX = {posX}, posY = {posY}, clienteRecogido = {clienteRecogido}, clienteARecoger = {clienteARecoger}, idLocalizacion = {idLocalizacion}, estadoSensores = {estadoSensores}")

def calcularMovimientos(X, Y, destX, destY):
    try :

        delta_x = int(destX) - int(posX)
        delta_y = int(destY) - int(posY)

        step_x = 1 if delta_x > 0 else -1 if delta_x < 0 else 0
        step_y = 1 if delta_y > 0 else -1 if delta_y < 0 else 0

        X = int(X) + step_x
        Y = int(Y) + step_y

        return X, Y

    except Exception as e:
        raise Exception(f"Error al calcular los movimientos: {e}")

def manejarMovimientos():
    global posX, posY, destX, destY, cltX, cltY, clienteRecogido, clienteARecoger, idLocalizacion, irBase

    try:
        while True:
            if estadoSensores:
                #printDebug("Iteración manejar movimientos.")
                #printDebug(f"{clienteRecogido}, {cltX}, {cltY}")
                # Mover hacia el cliente
                if irBase:
                    try:
                        while (int(posX) != 1 or int(posY) != 1):
                            if not irBase:
                                break
                            x, y = calcularMovimientos(posX, posY, 1, 1)
                            mover(x, y)
                            time.sleep(1)
                    except Exception as e:
                        raise Exception(f"Error al mover hacia la base. {e}")
                else:
                    if not clienteRecogido and cltX is not None and cltY is not None:
                        try:
                            while (int(posX) != int(cltX) or int(posY) != int(cltY)):
                                if irBase or not estadoSensores:
                                    break
                                x, y = calcularMovimientos(posX, posY, cltX, cltY)
                                mover(x, y)
                                time.sleep(1)  # Esperar un segundo entre movimientos
                            if not irBase and estadoSensores:
                                clienteRecogido = True
                                printInfo("Cliente recogido.")
                                if clienteRecogido:
                                    publicarMensajeEnTopic(f"[EC_DE_{ID}->EC_Central][{token}][SERVICIO][CLIENTE_RECOGIDO][{clienteARecoger}][{idLocalizacion}]", TOPIC_TAXIS, BROKER_ADDR, BROKER_KEY)
                                else: #TODO: NUNCA SE VA A EJECUTAR??'
                                    publicarMensajeEnTopic(f"[EC_DE_{ID}->EC_Central][{token}][SERVICIO][CLIENTE_RECOGIDO][{None}][{None}]", TOPIC_TAXIS, BROKER_ADDR, BROKER_KEY)
                        except Exception as e:
                            raise Exception(f"PARTE 2: Error al mover hacia el cliente. {e}")
                    # Mover hacia el destino del cliente
                    elif clienteRecogido and destX is not None and destY is not None:
                        try:

                            x, y = calcularMovimientos(posX, posY, destX, destY)
                            while (int(posX) != int(destX) or int(posY) != int(destY)):
                                if not estadoSensores:
                                    break
                                x, y = calcularMovimientos(posX, posY, destX, destY)
                                mover(x, y)
                                time.sleep(1)  # Esperar un segundo entre movimientos

                            if estadoSensores:
                                printInfo("Destino alcanzado.")
                                publicarMensajeEnTopic(f"[EC_DE_{ID}->EC_Central][{token}][SERVICIO][CLIENTE_EN_DESTINO][{clienteARecoger}][{x},{y}][{idLocalizacion}]", TOPIC_TAXIS, BROKER_ADDR, BROKER_KEY)
                                clienteRecogido = False
                                clienteARecoger = None
                                destX, destY, cltX, cltY = None, None, None, None
                        except Exception as e:
                            raise Exception(f"Error al mover hacia el destino. {e}")

                if posX == 1 and posY == 1 and irBase:
                    desconectar()

                    time.sleep(1)  # Control de la tasa del bucle principal
            else:
                printInfo("Sensores no operativos. No se puede realizar el movimiento.")
                time.sleep(5)
    except Exception as e:
        pass
        printError(f"Excepción {type(e)} inesperada en manejarMovimientos(): {e}")

def autenticarEnCentral():
    hiloSocketCentral = threading.Thread(target=gestionarConexionCentral)
    hiloSocketCentral.start()

    hiloBroker = threading.Thread(target=gestionarBroker)
    hiloBroker.start()

    # Probablemente mandemos un primer estado antes de tener token, pero no importa
    # ya que en la propia autentificación mandamos el estado. Aún así, para
    # evitar situaciones en las que el estado cambie entre login y recepción de token:
    while token == None:
        pass
    hiloEstado = threading.Thread(target=gestionarEstado)
    hiloEstado.start()

def desconectar():
    printInfo("Desconectando...")
    os.execv(sys.executable, [sys.executable] + sys.argv)

def registrarTaxi():
    try:
        print("Intentando registrar el taxi...")

        # Llamada al endpoint de registro
        response = requests.put(f"{API_URL}/registrar/{ID}", verify=False)

        # Si la respuesta tiene un código de éxito
        if response.status_code == 201:
            mensaje = response.json().get("message", response.text)
            print(f"{mensaje}")
        else:
            # Manejo de errores
            error_message = response.json().get("error", response.text)
            print(f"Error al registrar el taxi: {error_message}")
    except requests.RequestException as e:
        print(f"Error de conexión al API: {e}")

def darDeBaja():
    try:
        print("Intentando dar de baja el registrar el taxi...")

        # Llamada al endpoint de registro
        response = requests.delete(f"{API_URL}/borrarTaxi/{ID}", verify=False)

        # Si la respuesta tiene un código de éxito
        if response.status_code == 200:
            print(f"Taxi eliminado exitosamente.")
        else:
            # Manejo de errores
            error_message = response.json().get("error", response.text)
            print(f"Error al dar de baja el taxi: {error_message}")
    except requests.RequestException as e:
        print(f"Error de conexión al API: {e}")

def main():
    while True:
        print(f"{COLORES_ANSI.BLUE}=== Menú de Taxi {ID} ===")

        print("Seleccione una opción:")
        print("1. Registrar")
        print("2. Dar de Baja")
        print("3. Autenticar")
        print(f"4. Salir{COLORES_ANSI.END_C}")
        opcion = input("Opción: ")

        if opcion == "1":
            print("Registrando Taxi...")
            registrarTaxi()
        elif opcion == "2":
            print("Dando de Baja Taxi...")
            darDeBaja()
        elif opcion == "3":
            print("Autenticando Taxi...")
            autenticarEnCentral()
        elif opcion == "4":
            print("Saliendo...")
        else:
            print("Opción no válida. Intente de nuevo.")

if __name__ == "__main__":
    comprobarArgumentos(sys.argv)
    asignarConstantes(sys.argv)

    hiloSocketSensores = threading.Thread(target=gestionarSocketSensores)
    hiloSocketSensores.start()

    main()
