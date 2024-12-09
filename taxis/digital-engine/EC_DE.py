import sys
import re
import socket
import threading
import json
from kafka import KafkaProducer, KafkaConsumer
import time
import os

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
TOKEN = None
API_URL = "http://localhost:5001"

sensoresConectados = 0
sensoresOk = 0
estadoSensores = False
mapa = Map()

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
    if len(argumentos) != 7:
        #print("CHECKS: ERROR LOS ARGUMENTOS. Necesito estos argumentos: <CENTRAL_IP> <CENTRAL_PORT> <BROKER_IP> <BROKER_PORT> <SENSOR_IP> <SENSOR_PORT> <ID>")
        printError("Necesito estos argumentos: <CENTRAL_IP> <CENTRAL_PORT> <BROKER_IP> <BROKER_PORT> <LISTEN_PORT> <ID>")
        exit()
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
    printInfo("Constantes asignadas.")

def gestionarEstado():
    global estadoSensores

    while True:
        if estadoSensores == True and (sensoresOk != sensoresConectados or sensoresConectados < 1):
            estadoSensores = False
            publicarMensajeEnTopic(f"[EC_DE_{ID}->EC_Central][SENSORES][KO]", TOPIC_TAXIS, BROKER_ADDR)
        elif estadoSensores == False and sensoresConectados > 0 and sensoresOk == sensoresConectados:
            estadoSensores = True
            publicarMensajeEnTopic(f"[EC_DE_{ID}->EC_Central][SENSORES][OK]", TOPIC_TAXIS, BROKER_ADDR)
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
        except:
            printError(f"Excepción {type(e)} en gestionarSensor().")

def recibirMapaLogin(socket):
    try:
        mensaje = recibirMensajeClienteSilent(socket)
        camposMensaje = re.findall('[^\[\]]+', mensaje)
        printInfo("Mapa recibido:")
        mapa.loadJson(camposMensaje[1])
        mapa.loadActiveTaxis(camposMensaje[2])
        mapa.print()
        return True
    except Exception as e:
        printError(f"Excepción {type(e)} al recibir el mapa: {e}.")
        return False

def gestionarConexionCentral():
    global posX, posY, cltX, cltY, destX, destY, clienteARecoger

    while True:
        try:
            socket = abrirSocketCliente(CENTRAL_ADDR)
            printInfo("Intentando autenticar en central.")
            if estadoSensores:
                enviarMensajeCliente(socket, f"[EC_DE_{ID}->EC_Central][AUTH_REQUEST][OK][{posX},{posY}][{clienteARecoger}][{clienteRecogido}][{TOKEN}]")
            else:
                enviarMensajeCliente(socket, f"[EC_DE_{ID}->EC_Central][AUTH_REQUEST][KO][{posX},{posY}][{clienteARecoger}][{clienteRecogido}][{TOKEN}]")
            
            #TODO: ¿Esto es necesario?
            time.sleep(0.2)

            while True:
                mensaje = recibirMensajeCliente(socket)
                if mensaje == None:
                    printWarning(f"Se ha perdido la conexión con EC_Central.")
                    break
                else:
                    camposMensaje = re.findall('[^\[\]]+', mensaje)
                    if mensaje.startswith(f"[EC_Central->EC_DE_{ID}][AUTHORIZED]"):

                        printInfo("Autentificación correcta.")
                        posX = camposMensaje[2].split(",")[0]
                        posY = camposMensaje[2].split(",")[1]

                        if not recibirMapaLogin(socket):
                            break # Se ha perdido conexión con el sensor durante el envío del mapas
                        hiloMovimientos = threading.Thread(target=manejarMovimientos)
                        hiloMovimientos.start()
                        
                        if camposMensaje[3] != "None":
                            clienteARecoger = camposMensaje[3]
                            cltX, cltY = obtenerPosicion(camposMensaje[3], True)

                        if camposMensaje[4] != "None":
                            destX, destY = obtenerPosicion(camposMensaje[4], False)
                        
                    elif mensaje == f"[EC_Central->EC_DE_{ID}][NOT_AUTHORIZED]":
                        printError("ENGINE: Autentificación incorrecta. Finalizando ejecución.")
                        os._exit(1)
                        #exit()
                    else:
                        printError(f"ENGINE: MENSAJE DESCONOCIDO: {mensaje}")
        except BrokenPipeError as error:
            printWarning("Se ha perdido la conexión con EC_Central.")
        except ConnectionRefusedError as error:
            printWarning("No se ha podido conectar con EC_Central.")
        except ConnectionResetError as error:
            printError("Algo ha ocurrido en EC_Central.")
        except Exception as e:
            printWarning(f"Excepción {type(e)} inesperada en gestionarConexionCentral(): {e}.")
        finally:
            time.sleep(3)
            printInfo(f"Reintentando conexión...")
            
        #Una vez autorizados y con posición, esperar a que se nos indique un servicio

def gestionarBroker():
    global mapa, cltX, cltY, destX, destY, clienteARecoger, idLocalizacion, irBase, clienteRecogido

    printInfo(f"Conectando al broker en la dirección ({BROKER_ADDR}) como consumidor.")
    consumidor = conectarBrokerConsumidor(BROKER_ADDR, TOPIC_TAXIS)
    while True:
        for mensaje in consumidor:
            printDebug(f"Mensaje recibido: {mensaje.value.decode(FORMAT)}")
            camposMensaje = re.findall('[^\[\]]+', mensaje.value.decode(FORMAT))
            #print(camposMensaje)
            if camposMensaje[0] == (f"EC_DE_{ID}->EC_Central"):
                pass
            elif camposMensaje[0] == ("EC_Central->ALL"):
                mapa.loadJson(camposMensaje[1])
                mapa.loadActiveTaxis(camposMensaje[2])
                mapa.print()
            elif camposMensaje[0] == f"EC_Central->BASE":
                if camposMensaje[1] == "SI":
                    irBase = True
                elif camposMensaje[1] == "NO":
                    irBase = False
            elif camposMensaje[0] == f"EC_Central->EC_DE_{ID}":
                if camposMensaje[1] == "SERVICIO":
                    clienteARecoger = camposMensaje[2].split("->")[0]
                    idLocalizacion = camposMensaje[2].split("->")[1]
                    cltX, cltY = obtenerPosicion(clienteARecoger, True)
                    destX, destY = obtenerPosicion(idLocalizacion, False)
            else:
                # TODO: Informar mas que decir que error
                pass
                printInfo(f"Mensaje desconocido descartado: {mensaje}.")


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
    global posX, posY, clienteRecogido, clienteARecoger, idLocalizacion, estadoSensores

    if (x > 20) or (x < 0) or (y > 20) or (y < 0):
        printError("Movimiento demasiado grande")
    elif (x == posX) and (y == posY):
        pass
    elif not estadoSensores:
        printError("Sensores no operativos. No se puede realizar el movimiento")
    else:
        posX = x
        posY = y

        printInfo(f"Moviendo a dirección ({x},{y})")        
        """publicarMensajeEnTopic(f"[EC_DE_{ID}->EC_Central][MOVIMIENTO][{x},{y}][{clienteARecoger}]", TOPIC_TAXIS, BROKER_ADDR)"""

        if clienteRecogido:
            publicarMensajeEnTopic(f"[EC_DE_{ID}->EC_Central][MOVIMIENTO][{x},{y}][{clienteARecoger}][{idLocalizacion}]", TOPIC_TAXIS, BROKER_ADDR)
        else:
            publicarMensajeEnTopic(f"[EC_DE_{ID}->EC_Central][MOVIMIENTO][{x},{y}][{None}][{None}]", TOPIC_TAXIS, BROKER_ADDR)

def calcularMovimientos(X, Y, destX, destY):

    delta_x = int(destX) - int(posX)
    delta_y = int(destY) - int(posY)

    step_x = 1 if delta_x > 0 else -1 if delta_x < 0 else 0
    step_y = 1 if delta_y > 0 else -1 if delta_y < 0 else 0

    X = int(X) + step_x
    Y = int(Y) + step_y

    return X, Y

def manejarMovimientos():
    global posX, posY, destX, destY, cltX, cltY, clienteRecogido, clienteARecoger, idLocalizacion, irBase

    try:
        while True:
            if estadoSensores:
                #printDebug("Iteración manejar movimientos.")
                #printDebug(f"{clienteRecogido}, {cltX}, {cltY}")
                # Mover hacia el cliente
                if irBase:
                    while (int(posX) != 1 or int(posY) != 1):
                        if not irBase:
                            break
                        x, y = calcularMovimientos(posX, posY, 1, 1)
                        mover(x, y)
                        time.sleep(1)
                else:
                    if not clienteRecogido and cltX is not None and cltY is not None:
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
                                publicarMensajeEnTopic(f"[EC_DE_{ID}->EC_Central][SERVICIO][CLIENTE_RECOGIDO][{clienteARecoger}][{idLocalizacion}]", TOPIC_TAXIS, BROKER_ADDR)
                            else: #TODO: NUNCA SE VA A EJECUTAR??'
                                publicarMensajeEnTopic(f"[EC_DE_{ID}->EC_Central][SERVICIO][CLIENTE_RECOGIDO][{None}][{None}]", TOPIC_TAXIS, BROKER_ADDR)

                    # Mover hacia el destino del cliente
                    elif clienteRecogido and destX is not None and destY is not None:
                        while (int(posX) != int(destX) or int(posY) != int(destY)):
                            if not estadoSensores:
                                break
                            x, y = calcularMovimientos(posX, posY, destX, destY)
                            mover(x, y)
                            time.sleep(1)  # Esperar un segundo entre movimientos
                
                        if estadoSensores:
                            printInfo("Destino alcanzado.")
                            publicarMensajeEnTopic(f"[EC_DE_{ID}->EC_Central][SERVICIO][CLIENTE_EN_DESTINO][{clienteARecoger}][{x},{y}][{idLocalizacion}]", TOPIC_TAXIS, BROKER_ADDR)
                            clienteRecogido = False
                            clienteARecoger = None
                            destX, destY, cltX, cltY = None, None, None, None

            time.sleep(1)  # Control de la tasa del bucle principal
    except Exception as e:
        printError(f"Excepción {type(e)} inesperada en manejarMovimientos(): {e}")


def autenticarEnCentral():
    hiloEstado = threading.Thread(target=gestionarEstado)
    hiloEstado.start()

    hiloSocketSensores = threading.Thread(target=gestionarSocketSensores)
    hiloSocketSensores.start()

    hiloSocketCentral = threading.Thread(target=gestionarConexionCentral)
    hiloSocketCentral.start()

    hiloBroker = threading.Thread(target=gestionarBroker)
    hiloBroker.start()

def registrarTaxi():
    global TOKEN  # Indicamos que TOKEN es una variable global
    try:
        print("Intentando registrar el taxi...")

        # Datos a enviar al endpoint
        payload = {"id": ID}

        # Llamada al endpoint de registro
        response = requests.put(f"{API_URL}/registrar", json=payload)

        # Si la respuesta tiene un código de éxito
        if response.status_code == 201:
            data = response.json()
            TOKEN = data["token"]  # Guardar el token en la constante global
            print(f"Taxi registrado exitosamente. Token recibido: {TOKEN}")
        else:
            # Manejo de errores
            error_message = response.json().get("error", response.text)
            print(f"Error al registrar el taxi: {error_message}")
    except requests.RequestException as e:
        print(f"Error de conexión al API: {e}")

def darDeBaja():
    global TOKEN  # Indicamos que TOKEN es una variable global
    try:
        print("Intentando dar de baja el registrar el taxi...")

        # Llamada al endpoint de registro
        response = requests.delete(f"{API_URL}/borrarTaxi/{ID}")

        # Si la respuesta tiene un código de éxito
        if response.status_code == 200:
            TOKEN = None
            print(f"Taxi eliminado exitosamente.")
        else:
            # Manejo de errores
            error_message = response.json().get("error", response.text)
            print(f"Error al registrar el taxi: {error_message}")
    except requests.RequestException as e:
        print(f"Error de conexión al API: {e}")

def main():
    while True:
        print(f"=== Menú de Taxi {ID}===")
        print(f"TOKEN: {TOKEN}")
        print("Seleccione una opción:")
        print("1. Registrar")
        print("2. Dar de Baja")
        print("3. Autenticar")
        print("4. Salir")
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
            main()

if __name__ == "__main__":
    comprobarArgumentos(sys.argv)
    asignarConstantes(sys.argv)

    main()
