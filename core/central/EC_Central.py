import sys
import time
import json
import re
import socket
import threading
from kafka import KafkaConsumer, KafkaProducer
import mariadb
from flask import Flask
from flask_cors import CORS
from datetime import datetime
import os
import requests
import uuid

sys.path.append('../../shared')
from EC_Shared import *
from EC_Map import Map
from EC_Map import iniciarMapa

HOST = '' # Simbólico, nos permite escuchar en todas las interfaces de red
LISTEN_PORT = None
THIS_ADDR = None

BROKER_IP = None
BROKER_PORT = None
BROKER_ADDR = None

DATABASE_USER = 'ec_central'
DATABASE_PASSWORD = 'sd2024_central'

WEATHER_IP = None
WEATHER_PORT = None

BROADCAST_TOKEN = str(uuid.uuid4())

taxisConectados = [] # [1, 2, 3, 5]
taxisLibres = [] # [2, 3]
taxisEnBase = []
mapa = Map()
irBase = False
climaAdverso = False

app = Flask(__name__)
CORS(app)

def comprobarArgumentos(argumentos):
    if len(argumentos) != 6:
        exitFatal("Necesito estos argumentos: <LISTEN_PORT> <BROKER_IP> <BROKER_PORT> <WEATHER_IP> <WEATHER_PORT>")        
    printInfo("Número de argumentos correcto.")

def asignarConstantes(argumentos):
    global HOST
    global LISTEN_PORT
    LISTEN_PORT = int(argumentos[1])
    global THIS_ADDR
    THIS_ADDR =  (HOST, LISTEN_PORT)
    global BROKER_IP
    BROKER_IP = argumentos[2]
    global BROKER_PORT
    BROKER_PORT = int(argumentos[3])
    global BROKER_ADDR
    BROKER_ADDR = BROKER_IP+":"+str(BROKER_PORT)
    global WEATHER_IP
    WEATHER_IP = argumentos[4]
    global WEATHER_PORT
    WEATHER_PORT = int(argumentos[5])
    printInfo("Constantes asignadas.")

def obtenerIP(ID):
    try:
        conexion, cursor = generarConexionBBDD(DATABASE_USER, DATABASE_PASSWORD)

        if ID.isdigit():
            cursor.execute("SELECT IP FROM taxis WHERE id = ?", (ID,))
        else:
            cursor.execute("SELECT IP FROM clientes WHERE id = ?", (ID,))

        resultado = cursor.fetchone()
        if resultado:
            return resultado[0]
        else:
            printError(f"No se encontró IP para el ID {ID}.")
            return None
    except mariadb.Error as e:
        printError(f"Error al obtener IP: {e}")
        return None
    finally:
        conexion.close()

    fecha_actual = datetime.now().strftime("%Y-%m-%d")
    nombre_archivo = f"log/logs_{fecha_actual}.log"
    os.makedirs(os.path.dirname(nombre_archivo), exist_ok=True)

    with open(nombre_archivo, "a") as archivo_log:
        archivo_log.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} [{IP}]- {message}\n")
        print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} [{IP}]- {message}")

def leerConfiguracionMapa():
    global diccionarioLocalizaciones
    try:
        with open('./resources/EC_locations.json') as json_file:
            jsonLocalizaciones = json.load(json_file)
            for key in jsonLocalizaciones:
                value = jsonLocalizaciones[key]
                for item in value:
                    mapa.setPosition(f"localizacion_{item['Id']}", item['POS'].split(",")[0], item['POS'].split(",")[1])
                    #printDebug(f"Cargada localización {item['Id']} con coordenadas ({item['POS']}).")
            printInfo("Mapa cargado con éxito desde fichero.")
    except IOError as error:
        exitFatal("No se ha podido abrir el fichero.")

def leerBBDD():
    conexion, cursor = generarConexionBBDD(DATABASE_USER, DATABASE_PASSWORD)

    cursor.execute("SELECT id, posicion FROM taxis")
    taxis = cursor.fetchall()
    for taxi in taxis:
        mapa.setPosition(f"taxi_{taxi[0]}", int(taxi[1].split(",")[0]), int(taxi[1].split(",")[1]))
        #printDebug(f"Cargado taxi {taxi[0]} con posición {taxi[1]}.")
    printInfo(f"Ubiación taxis cargada desde BBDD.")

    cursor.execute("SELECT id, posicion FROM clientes")
    clientes = cursor.fetchall()
    for cliente in clientes:
        mapa.setPosition(f"cliente_{cliente[0]}", int(cliente[1].split(",")[0]), int(cliente[1].split(",")[1]))
        #printInfo(f"Cargado cliente {cliente[0]} con posición {cliente[1]}.")
    printInfo(f"Ubiación clientes cargada desde BBDD.")
    dbToJSON()
    conexion.close()

def dbToJSON():
    conexion, cursor = generarConexionBBDD(DATABASE_USER, DATABASE_PASSWORD)

    try:
        # Consultar datos de la tabla de taxis
        cursor.execute("SELECT id, estado, sensores, posicion, cliente, destino FROM taxis")
        taxis = [
            {
                "id": row[0],
                "estado": row[1],
                "sensores": row[2],
                "posicion": row[3],
                "cliente": row[4],
                "destino": row[5]
            }
            for row in cursor.fetchall()
        ]

        # Consultar datos de la tabla de clientes
        cursor.execute("SELECT id, posicion FROM clientes")
        clientes = [
            {
                "id": row[0],
                "posicion": row[1]
            }
            for row in cursor.fetchall()
        ]

        # Crear el objeto JSON
        data = {
            "taxis": taxis,
            "clientes": clientes
        }

        # Convertir el objeto data a una cadena JSON con formato
        json_data = json.dumps(data, indent=4)

        printInfo("Enviando estado de la BBDD a traves del broker.")
        publicarMensajeEnTopicSilent(json_data, TOPIC_ESTADOS_MAPA, BROKER_ADDR)
    except Exception as e:
        print(f"Error al convertir la base de datos a JSON: {e}")
        return None

    finally:
        # Cerrar la conexión a la base de datos
        conexion.close()


def exportDB():
    conexion, cursor = generarConexionBBDD(DATABASE_USER, DATABASE_PASSWORD)

    try:
        # Consultar datos de la tabla de taxis
        cursor.execute("SELECT id, estado, sensores, posicion, cliente, destino FROM taxis")
        taxis = [
            {
                "id": row[0],
                "estado": row[1],
                "sensores": row[2],
                "posicion": row[3],
                "cliente": row[4],
                "destino": row[5]
            }
            for row in cursor.fetchall()
        ]

        # Consultar datos de la tabla de clientes
        cursor.execute("SELECT id, posicion FROM clientes")
        clientes = [
            {
                "id": row[0],
                "posicion": row[1]
            }
            for row in cursor.fetchall()
        ]


        with open('./resources/EC_locations.json') as json_file:
            jsonLocalizaciones = json.load(json_file)
            
        # Crear el objeto JSON
        data = {
            "taxis": taxis,
            "clientes": clientes,
            "localizaciones": jsonLocalizaciones
        }
        
        # Convertir el objeto data a una cadena JSON con formato
        json_data = json.dumps(data, indent=4)

        return json_data 
    except Exception as e:
        print(f"Error al exportar la base de datos: {e}")
        return None

    finally:
        # Cerrar la conexión a la base de datos
        conexion.close()


def ejecutarSentenciaBBDD(sentencia, user, password):
    resultado = None

    try:
        conexion, cursor = generarConexionBBDD(user, password)
        cursor.execute(sentencia)
        printInfo(f"Sentencia {sentencia} ejecutada sobre la BBDD.")
        if not sentencia.startswith("UPDATE"):
            try:
                resultado = cursor.fetchall()
            except mariadb.ProgrammingError as e:
                printWarning(f"La consulta '{sentencia}' no ha producido resultados.")
        conexion.commit()
        conexion.close()
        
        #Enviar actualización de la bbdd
        #dbToJSON()
        
        return resultado
    except Exception as e:
        # Base de datos no tiene que ser resiliente
        exitFatal(f"{threading.current_thread().name} - No se pudo conectar a la base de datos. {e.__class__}: {e}")

def gestionarBrokerClientes():
    global diccionarioLocalizaciones
    global taxisLibres, taxisConectados

    consumidor = conectarBrokerConsumidor(BROKER_ADDR, TOPIC_CLIENTES) # ,auto_offset_reset='earliest')

    try:
        for mensaje in consumidor:
            #printDebug(f"Mensaje recibido en TOPIC_CLIENTES: {mensaje.value.decode(FORMAT)}")
            camposMensaje = re.findall('[^\[\]]+', mensaje.value.decode(FORMAT))

            if camposMensaje[0].startswith("EC_Central"):
                pass
            elif camposMensaje[0].startswith("EC_Customer"):
                # ['EC_Customer_a->EC_Central', 'E']
                time.sleep(0.5) # Evitar que pueda terminar el servicio antes de que el customer esté conectado al broker
                idCliente = camposMensaje[0].split("->")[0][12:]
                localizacion = camposMensaje[1]
                printInfo(f"Solicitud de servicio recibida, cliente {idCliente}, destino {localizacion}.")

                if mapa.getPosition(f"localizacion_{localizacion}") is None:
                    printWarning(f"La localización {localizacion} no existe. Cancelando servicio a cliente {idCliente}.")
                    publicarMensajeEnTopic(f"[EC_Central->EC_Customer_{idCliente}][KO]", TOPIC_CLIENTES, BROKER_ADDR)
                else:
                    #ejecutarSentenciaBBDD(f"UPDATE clientes SET IP = '{mensaje.key.decode(FORMAT)}' WHERE id = '{idCliente}'", DATABASE_USER, DATABASE_PASSWORD)
                    printDebug(f"Estado de los taxis (Conectados, Libres): {taxisConectados}, {taxisLibres}.")
                    if len(taxisLibres) < 1:
                        printWarning(f"No hay taxis disponibles. Cancelando servicio a cliente {idCliente}.")
                        publicarMensajeEnTopic(f"[EC_Central->EC_Customer_{idCliente}][KO]", TOPIC_CLIENTES, BROKER_ADDR)
                    else:
                        taxiElegido = taxisLibres.pop()
                        printInfo(f"Asignando servicio del cliente {idCliente} al taxi {taxiElegido}.")
                        mapa.activateTaxi(taxiElegido)
                        publicarMensajeEnTopic(f"[EC_Central->EC_DE_{taxiElegido}][{BROADCAST_TOKEN}][SERVICIO][{idCliente}->{localizacion}]", TOPIC_TAXIS, BROKER_ADDR)

                        ejecutarSentenciaBBDD(f"UPDATE taxis SET estado = 'enCamino' WHERE id = {taxiElegido}", DATABASE_USER, DATABASE_PASSWORD)
                        ejecutarSentenciaBBDD(f"UPDATE taxis SET cliente = '{idCliente}' WHERE id = {taxiElegido}", DATABASE_USER, DATABASE_PASSWORD)
                        ejecutarSentenciaBBDD(f"UPDATE taxis SET destino = '{localizacion}' WHERE id = {taxiElegido}", DATABASE_USER, DATABASE_PASSWORD)

                        publicarMensajeEnTopic(f"[EC_DE_{taxiElegido}] Servicio asignado [{idCliente}->{localizacion}]", TOPIC_ERRORES_MAPA, BROKER_ADDR)
                        printInfo(f"[EC_DE_{taxiElegido}] Servicio asignado [{idCliente}->{localizacion}]")
                        #printLog(taxiElegido, f"Servicio asignado [{idCliente}->{localizacion}]")
        else:
            #printInfo(mensaje)
            #printInfo(mensaje.value.decode(FORMAT))
            printError("Mensaje desconocido recibido en {TOPIC_CLIENTES} : {mensaje.value.decode(FORMAT)}.")
    except Exception as e:
        exitFatal(f"Excepción producida al gestionar el broker de los clientes: {e}")

def gestionarBrokerTaxis():
    global BROKER_ADDR, taxisLibres
    consumidor = conectarBrokerConsumidor(BROKER_ADDR, TOPIC_TAXIS)

    for mensaje in consumidor:
        camposMensaje = re.findall('[^\[\]]+', mensaje.value.decode(FORMAT))
        #printDebug(camposMensaje)
        #printInfo(camposMensaje)
        #printInfo(mensaje)
        if camposMensaje[0].startswith("EC_Central"):
            #Nuestros propios mensajes
            pass
        elif camposMensaje[0].startswith("EC_DE"):
            idTaxi = camposMensaje[0].split("->")[0][6:]

            if camposMensaje[1] == "":
                printInfo(f"Taxi {idTaxi} ha enviado un mensaje sin token. Ignorando...")
                pass
            elif not verifiarTokenTaxi(idTaxi, camposMensaje[1]):
                printInfo(f"Taxi {idTaxi} ha enviado un mensaje con un token erróneo. Ignorando...")
                pass

            elif camposMensaje[2] == "AUTH_REQUEST":
                pass #Aquí no nos importa

            elif camposMensaje[2] == "SENSORES":
                # ['EC_DE_1->EC_Central', 'SENSORES', 'OK']
                estado = camposMensaje[3]
                printInfo(f"Taxi {idTaxi} ha cambiado su estado a {estado}.")
                if estado == "OK":
                    mapa.activateTaxi(idTaxi)
                elif estado == "KO":
                    mapa.deactivateTaxi(idTaxi)

                ejecutarSentenciaBBDD(f"UPDATE taxis SET sensores = '{estado}' WHERE id = {idTaxi}", DATABASE_USER, DATABASE_PASSWORD)
                publicarMensajeEnTopic(f"[EC_DE_{idTaxi}] Cambio su estado a: {estado}", TOPIC_ERRORES_MAPA, BROKER_ADDR)
                printInfo(f"[EC_DE_{idTaxi}] Cambio su estado a: {estado}")
                #printLog(idTaxi, f"Cambio su estado a: {estado}")

            elif camposMensaje[2] == "MOVIMIENTO":
                # ['EC_DigitalEngine-1->EC_Central', '(1,2)']
                posX = int(camposMensaje[3].split(",")[0])
                posY = int(camposMensaje[3].split(",")[1])
                printInfo(f"Movimiento ({posX},{posY}) recibido del taxi {idTaxi}.")
                ejecutarSentenciaBBDD(f"UPDATE taxis SET posicion = '{posX},{posY}' WHERE id = {idTaxi}", DATABASE_USER, DATABASE_PASSWORD)
                # Si el taxi tiene un cliente, moverlo también
                taxiBBDD = ejecutarSentenciaBBDD(f"SELECT * FROM taxis WHERE id = {idTaxi}", DATABASE_USER, DATABASE_PASSWORD)
                if taxiBBDD[0][1] == "servicio":
                    idCliente = taxiBBDD[0][4]
                    ejecutarSentenciaBBDD(f"UPDATE clientes SET posicion = '{posX},{posY}' WHERE id = '{idCliente}'", DATABASE_USER, DATABASE_PASSWORD)
                    mapa.move(f"cliente_{idCliente}", posX, posY)

                mapa.move(f"taxi_{idTaxi}", posX, posY)
                mapa.print()

                publicarMensajeEnTopic(f"[EC_Central->ALL][{BROADCAST_TOKEN}][{mapa.exportJson()}][{mapa.exportActiveTaxis()}]", TOPIC_TAXIS, BROKER_ADDR)
            elif camposMensaje[2] == "SERVICIO":
                if camposMensaje[3] == "CLIENTE_RECOGIDO":
                    publicarMensajeEnTopic(f"[EC_Central->EC_Customer_{camposMensaje[4]}][RECOGIDO]", TOPIC_CLIENTES, BROKER_ADDR)
                    ejecutarSentenciaBBDD(f"UPDATE taxis SET estado = 'servicio' WHERE id = {idTaxi}", DATABASE_USER, DATABASE_PASSWORD)
                    publicarMensajeEnTopic(f"[EC_DE_{idTaxi}] Recogido a su cliente {camposMensaje[4]}", TOPIC_ERRORES_MAPA, BROKER_ADDR)
                    printInfo(f"[EC_DE_{idTaxi}] Recogido a su cliente {camposMensaje[4]}")
                    #printLog(idTaxi, f"Recogido a su cliente {camposMensaje[4]}")
                    #actualizarEstadosJSON(True, camposMensaje[4], f"OK. Taxi {idTaxi}", camposMensaje[5])
                    #actualizarEstadosJSON(False, idTaxi, f"OK. Servicio {camposMensaje[4]}", camposMensaje[5]) # TAXI

                if camposMensaje[3] == "CLIENTE_EN_DESTINO":
                    posX = int(camposMensaje[5].split(",")[0])
                    posY = int(camposMensaje[5].split(",")[1])
                    idCliente = camposMensaje[4]

                    publicarMensajeEnTopic(f"EC_Central->EC_Customer_{idCliente}[EN_DESTINO]", TOPIC_CLIENTES, BROKER_ADDR)

                    mapa.deactivateTaxi(idTaxi)
                    publicarMensajeEnTopic(f"[EC_DE_{idTaxi}] Llevado al cliente {camposMensaje[4]} a su destino", TOPIC_ERRORES_MAPA, BROKER_ADDR)
                    printInfo(f"[EC_DE_{idTaxi}] Llevado al cliente {camposMensaje[4]} a su destino")
                    #printLog(idTaxi, f"Llevado al cliente {camposMensaje[3]} a su destino")
                    #actualizarEstadosJSON(True, camposMensaje[3], "OK. En destino", camposMensaje[4]) # CLIENTE
                    #actualizarEstadosJSON(False, idTaxi, "OK. Parado") # TAXI

                    taxisLibres.append(idTaxi)
                    ejecutarSentenciaBBDD(f"UPDATE taxis SET estado = 'esperando' WHERE id = {idTaxi}", DATABASE_USER, DATABASE_PASSWORD)
                    ejecutarSentenciaBBDD(f"UPDATE taxis SET cliente = NULL WHERE id = {idTaxi}", DATABASE_USER, DATABASE_PASSWORD)
                    ejecutarSentenciaBBDD(f"UPDATE taxis SET destino = NULL WHERE id = {idTaxi}", DATABASE_USER, DATABASE_PASSWORD)
        else:
            #printInfo(mensaje)
            #printInfo(mensaje.value.decode(FORMAT))
            printError(f"Mensaje desconocido recibido en {TOPIC_TAXIS} : {mensaje.value.decode(FORMAT)}.")

def comprobarTaxi(idTaxi):
    try:
        conexion, cursor = generarConexionBBDD(DATABASE_USER, DATABASE_PASSWORD)

        cursor.execute("SELECT id FROM taxis WHERE id = ?", (idTaxi,))
        resultado = cursor.fetchone()

        if resultado is None:
            printInfo(f"Taxi {idTaxi} no encontrado en la base de datos.")
            return False
        else:
            if idTaxi in taxisConectados:
                printInfo(f"Taxi {idTaxi} existe y ya está conectado.")
                return False
            else:
                printInfo(f"Taxi {idTaxi} comprobado con éxito.")
                return True
    except Exception as e:
        printError(e)
        return False

def verifiarTokenTaxi(idTaxi, tokenTaxi):
    try:
        conexion, cursor = generarConexionBBDD(DATABASE_USER, DATABASE_PASSWORD)

        cursor.execute("SELECT token FROM taxis WHERE id = ?", (idTaxi,))
        resultado = cursor.fetchone()

        if resultado is None:
            printError(f"Taxi {idTaxi} no encontrado en la base de datos al verificar token.")
            return False
        elif tokenTaxi == resultado[0]:
            printDebug("Token del taxi correcto")
            return True
        else:
            printDebug("Token del taxi incorrecto")
            return False

    except Exception as e:
        printError(e)
        return False

def autenticarTaxi(conexion, direccion):
    tokenTaxi = str(uuid.uuid4())

    mensaje = recibirMensajeCliente(conexion)
    if mensaje is None:
        printWarning("Perdida conexión con un taxi durante la autentificación.")
        return -1

    camposMensaje = re.findall('[^\[\]]+', mensaje)
    idTaxi = camposMensaje[0].split("->")[0][6:]
    if not comprobarTaxi(idTaxi):
        printInfo("Taxi no registrado o ya conectado. No autorizado.")
        enviarMensajeServidor(conexion, f"[EC_Central->EC_DE_{idTaxi}][NOT_AUTHORIZED]")
        return -1

    #printDebug(camposMensaje)

    ejecutarSentenciaBBDD(f"UPDATE taxis SET IP = '{direccion[0]}' WHERE id = {idTaxi}", DATABASE_USER, DATABASE_PASSWORD)
    ejecutarSentenciaBBDD(f"UPDATE taxis SET sensores = '{camposMensaje[2]}' WHERE id = {idTaxi}", DATABASE_USER, DATABASE_PASSWORD)
    ejecutarSentenciaBBDD(f"UPDATE taxis SET token = '{tokenTaxi}' WHERE id = {idTaxi}", DATABASE_USER, DATABASE_PASSWORD)
    #printDebug("Primeras sentencias ejecutadas")
    if camposMensaje[3] != "None,None":
        printInfo(f"El taxi {idTaxi} tenía posición, por lo tanto nosotros habíamos caído.")
        # Si el taxi estaba realizando un servicio en el momento de nuestra caída comprobar si lo ha finalizado y notificar al cliente
        ejecutarSentenciaBBDD(f"UPDATE taxis SET posicion = '{camposMensaje[3].split(',')[0]},{camposMensaje[3].split(',')[1]}' WHERE id = {idTaxi}", DATABASE_USER, DATABASE_PASSWORD)
        mapa.setPosition(f"taxi_{idTaxi}", camposMensaje[3].split(',')[0], camposMensaje[3].split(',')[1])
        if camposMensaje[4] != None:
            mapa.activateTaxi(idTaxi)
            if camposMensaje[5] == "True":
                ## El cliente ha sido recogido
                ejecutarSentenciaBBDD(f"UPDATE clientes SET posicion = '{camposMensaje[3].split(',')[0]},{camposMensaje[3].split(',')[1]}' WHERE id = {camposMensaje[4]}", DATABASE_USER, DATABASE_PASSWORD)
                mapa.setPosition(f"cliente_{camposMensaje[4]}", camposMensaje[3].split(',')[0], camposMensaje[3].split(',')[1])
                ejecutarSentenciaBBDD(f"UPDATE taxis SET estado = 'servicio' WHERE id = {idTaxi}", DATABASE_USER, DATABASE_PASSWORD)
            else:
                ejecutarSentenciaBBDD(f"UPDATE taxis SET estado = 'enCamino' WHERE id = {idTaxi}", DATABASE_USER, DATABASE_PASSWORD)
                if idTaxi in taxisLibres:
                    taxisLibres.remove(idTaxi)
    else:
        printInfo(f"El taxi {idTaxi} acaba de arrancar.")
    #[EC_Central->EC_DE_1][AUTHORIZED][1,2][Cliente][Destino]
    taxiBBDD = ejecutarSentenciaBBDD(f"SELECT * FROM taxis WHERE id = {idTaxi}", DATABASE_USER, DATABASE_PASSWORD)

    enviarMensajeServidor(conexion, f"[EC_Central->EC_DE_{idTaxi}][AUTHORIZED][{tokenTaxi}][{BROADCAST_TOKEN}][{taxiBBDD[0][3].split(',')[0]},{taxiBBDD[0][3].split(',')[1]}][{taxiBBDD[0][4]}][{taxiBBDD[0][5]}]")
    enviarMensajeServidor(conexion, f"[EC_Central->EC_DE_{idTaxi}][{BROADCAST_TOKEN}][{mapa.exportJson()}][{mapa.exportActiveTaxis()}]")

    publicarMensajeEnTopic(f"[EC_DE_{idTaxi}] Autorizado.", TOPIC_ERRORES_MAPA, BROKER_ADDR)
    printInfo(f"[EC_DE_{idTaxi}] Autorizado.")
    #printLog(idTaxi, f"Taxi {idTaxi} ha sido autorizado.")
    #actualizarEstadosJSON(False, idTaxi, "OK. Parado")
    return idTaxi


def gestionarTaxi(conexion, direccion):
    global taxisConectados, taxisLibres
    idTaxi = autenticarTaxi(conexion, direccion)

    #printDebug("Iniciando gestión.")

    if idTaxi != -1:
        taxisConectados.append(idTaxi)
        taxisLibres.append(idTaxi)
        while True:
            try:
                mensaje = recibirMensajeServidor(conexion)
                if mensaje == None:
                    printWarning(f"Conexión con el taxi en {direccion} perdida.")
                    break
                else:
                    printWarning(f"Mensaje del taxi {direccion} recibido: {mensaje}")
            except Exception as e:
                printError(f"Excepción {type(e)} en gestionarTaxi().")

        #Taxi ha caido
        taxisConectados.remove(idTaxi)
        if idTaxi in taxisLibres:
            taxisLibres.remove(idTaxi)
        else:
        #if taxiBBDD[0][1] == "enCamino" or taxiBBDD[0][1] == "servicio":
            cliente = ejecutarSentenciaBBDD(f"SELECT cliente FROM taxis WHERE id = {idTaxi}", DATABASE_USER, DATABASE_PASSWORD)[0][0]
            printWarning(f"Cancelando servicio a cliente {cliente} por caída de su taxi.")
            publicarMensajeEnTopic(f"[EC_Central->EC_Customer_{cliente}][KO]", TOPIC_CLIENTES, BROKER_ADDR)
            ejecutarSentenciaBBDD(f"UPDATE taxis SET cliente = NULL WHERE id = {idTaxi}", DATABASE_USER, DATABASE_PASSWORD)
            ejecutarSentenciaBBDD(f"UPDATE taxis SET destino = NULL WHERE id = {idTaxi}", DATABASE_USER, DATABASE_PASSWORD)

        mapa.deactivateTaxi(idTaxi)
        ejecutarSentenciaBBDD(f"UPDATE taxis SET estado = 'desconectado' WHERE id = {idTaxi}", DATABASE_USER, DATABASE_PASSWORD)
        ejecutarSentenciaBBDD(f"UPDATE taxis SET token = NULL WHERE id = {idTaxi}", DATABASE_USER, DATABASE_PASSWORD)

        mapa.print()

        publicarMensajeEnTopic(f"[EC_DE_{idTaxi}] Su conexión ha caido.", TOPIC_ERRORES_MAPA, BROKER_ADDR)
        printInfo(f"[EC_DE_{idTaxi}] Su conexión ha caido.")
        #printLog(idTaxi, "Su conexión ha caido.")

    else:
        printInfo(f"Taxi con conexion {conexion} y {direccion} no autorizado. Desconectando...")
        conexion.close()

def gestionarLoginTaxis():
    socketEscucha = abrirSocketServidor(THIS_ADDR)
    socketEscucha.listen()
    while True:
        conexion, direccion = socketEscucha.accept()
        hiloTaxi = threading.Thread(target=gestionarTaxi, args=(conexion, direccion))
        hiloTaxi.start()

def dirigirABaseATodos():
    global irBase

    estado_anterior = irBase

    while True:
        if climaAdverso:
            irBase = True
    
        if irBase:
            publicarMensajeEnTopic(f"[EC_Central->BASE][{BROADCAST_TOKEN}][ALL][SI]", TOPIC_TAXIS, BROKER_ADDR)
            publicarMensajeEnTopic(f"[EC_Central] Enviando todos los taxis a base", TOPIC_ERRORES_MAPA, BROKER_ADDR)
            printInfo("Enviando todos los taxis a base.")
            estado_anterior = True
            #printLog("ALL", "Enviando todos los taxis a base.")
        if not irBase and estado_anterior:
            publicarMensajeEnTopic(f"[EC_Central->BASE][{BROADCAST_TOKEN}][ALL][NO]", TOPIC_TAXIS, BROKER_ADDR)
            publicarMensajeEnTopic(f"[EC_Central] Los taxis pueden salir de base y continuar su servicio", TOPIC_ERRORES_MAPA, BROKER_ADDR)
            printInfo("Cancelando envío a base.")
            estado_anterior = False
            #printLog("ALL", "Cancelando envío a base.")
        time.sleep(1)

def dirigirTaxiABase(idTaxi):
    try:
        if idTaxi not in taxisConectados:
            printError(f"Taxi {idTaxi} no está conectado.")
            return

        if idTaxi in taxisEnBase:
            taxisEnBase.remove(idTaxi)
            publicarMensajeEnTopic(f"[EC_Central->BASE][{BROADCAST_TOKEN}][{idTaxi}][NO]", TOPIC_TAXIS, BROKER_ADDR)
            publicarMensajeEnTopic(f"[EC_Central] Los taxis pueden salir de base y continuar su servicio", TOPIC_ERRORES_MAPA, BROKER_ADDR)
            printInfo(f"Cancelando envio a la base del taxi {idTaxi}.")
            #printLog(idTaxi, "Cancelando envio a la base.")
        else:
            taxisEnBase.append(idTaxi)
            publicarMensajeEnTopic(f"[EC_Central->BASE][{BROADCAST_TOKEN}][{idTaxi}][SI]", TOPIC_TAXIS, BROKER_ADDR)
            publicarMensajeEnTopic(f"[EC_Central] Enviando taxi {idTaxi} a base", TOPIC_ERRORES_MAPA, BROKER_ADDR)
            printInfo(f"Enviando taxi {idTaxi} a la base.")
            #printLog(idTaxi, "Enviando a la base.")
    except Exception as e:
        raise e


def inputBase():
    global irBase

    threading.Thread(target=dirigirABaseATodos).start()

    while True:
        user_input = input(f"{COLORES_ANSI.BLUE}Introduce 'ALL' para enviar todos los taxis a base o un ID específico:{COLORES_ANSI.END_C}\n").strip()

        if user_input.upper() == "" or not user_input:
            continue
        if (not climaAdverso):
            if user_input.upper() == "ALL":
                irBase = not irBase
                if irBase:
                    printInfo("Se enviarán todos los taxis a la base.")
                else:
                    printInfo("El envío de taxis a la base ha sido cancelado.")
            else:
                taxiId = None
                try:
                    taxiId = int(user_input)
                    dirigirTaxiABase(taxiId)
                except Exception as e:
                    printError(f"Error con la ID '{taxiId}': {e}")
        else:
            printError("No se puede actuar sobre los taxis debido al clima adverso. Todos vuelven a base")


def verificarClima():
    global climaAdverso
    WEATHER_SERVER = f"http://{WEATHER_IP}:{WEATHER_PORT}/consultarClima"

    while True:
        try:
            response = requests.get(WEATHER_SERVER)
            printInfo("Petición para consultar clima.")
            #printLog("CENTRAL", "Petición para consultar clima.")
            if response.status_code == 200:
                data = response.json()
                if data["status"] == "KO":
                    climaAdverso = True
                    printWarning(data["message"])
                else:
                    climaAdverso = False
                    printInfo(data["message"])

                #printLog("CENTRAL", data["message"])
            else:
                printError("Error al consultar el clima.")
                climaAdverso = True
                #printLog("CENTRAL", "Error al consultar el clima.")
        except Exception as e:
            printWarning(f"Servidor de clima innacesible.")
            climaAdverso = True
            #printLog("CENTRAL", f"Servidor de clima innacesible.")
        finally:
            time.sleep(10)

### API
@app.route('/estadoActual-mapa', methods=['GET'])
def estadoActual():
    try:
        listado = exportDB()
        if listado:
            data = json.loads(listado)
            data["taxis"] = [taxi for taxi in data["taxis"] if taxi["estado"] != "desconectado"]
            listado = json.dumps(data, indent=4)

        return listado, 200
    except Exception as e:
        return f"Error al obtener el estado actual del mapa: {e}", 500


@app.route('/logs', methods=['GET'])
def obtenerLogs():
    fecha_actual = datetime.now().strftime("%Y-%m-%d")
    nombre_archivo = f"log/logs_{fecha_actual}.log"

    if os.path.exists(nombre_archivo):
        with open(nombre_archivo, "r") as archivo_log:
            contenido = archivo_log.read()
        return contenido, 200
    else:
        return "No hay logs disponibles para el día de hoy.", 404

def main():
    comprobarArgumentos(sys.argv)
    asignarConstantes(sys.argv)
    leerConfiguracionMapa()
    leerBBDD()

    printInfo("Mostrando mapa al momento del arranaque.")
    mapa.print()

    printInfo('TOKEN "Broadcast": ' + BROADCAST_TOKEN + '.')

    hiloClientes = threading.Thread(target=gestionarBrokerClientes)
    hiloClientes.start()

    hiloTaxis = threading.Thread(target=gestionarBrokerTaxis)
    hiloTaxis.start()

    hiloLoginTaxis = threading.Thread(target=gestionarLoginTaxis)
    hiloLoginTaxis.start()

    #hiloMapa = threading.Thread(target=iniciarMapa, args=(mapa, BROKER_ADDR,))
    #hiloMapa.start()

    hiloBase = threading.Thread(target=inputBase)
    hiloBase.start()

    # Iniciar el hilo para verificar el clima
    hiloClima = threading.Thread(target=verificarClima)
    hiloClima.start()

if __name__ == "__main__":
    printInfo("Iniciando EC_Central...")

    # Ejecuta el servidor Flask en un hilo separado
    hiloApi = threading.Thread(target=app.run, kwargs={'debug': True, 'use_reloader': False})
    hiloApi.start()

    # Llama al resto de tu lógica principal
    main()
