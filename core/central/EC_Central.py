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

sys.path.append('../../shared')
from EC_Shared import *
from EC_Map import Map
from EC_Map import iniciarMapa

DATABASE = './resources/database.db'

HOST = '' # Simbólico, nos permite escuchar en todas las interfaces de red
LISTEN_PORT = None
THIS_ADDR = None
BROKER_IP = None
BROKER_PORT = None
BROKER_ADDR = None
DATABASE_USER = 'ec_central'
DATABASE_PASSWORD = 'sd2024_central'

taxisConectados = [] # [1, 2, 3, 5]
taxisLibres = [] # [2, 3]
taxisEnBase = []
mapa = Map()
irBase = False
climaAdverso = False

app = Flask(__name__)
CORS(app)

def comprobarArgumentos(argumentos):
    if len(argumentos) != 4:
        printError("Necesito estos argumentos: <LISTEN_PORT> <BROKER_IP> <BROKER_PORT>")
        exit()
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
    printInfo("Constantes asignadas.")

def obtenerIP(ID):
    try:
        conexion, cursor = generarConexionBBDD(DATABASE_USER, DATABASE_PASSWORD)
        if conexion is None:
            exitFatal("OBTENer IP: No se ha podido conectar a la base de datos.")

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

# TODO: Eliminar una vez se vea que ya no es necesario
def printLog(ID, message):
    if ID == "ALL":
        IP = "BROADCAST"
    elif ID == "CENTRAL":
        IP = "CENTRAL"
    else:
        IP = obtenerIP(ID)

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

def ejecutarSentenciaBBDD(sentencia):
    try:
        conexion, cursor = generarConexionBBDD(DATABASE_USER, DATABASE_PASSWORD)
        cursor.execute(sentencia)
        resultado = cursor.fetchall()
        conexion.commit()
        conexion.close()
        dbToJSON()
        return resultado
    except Exception as a:
        printError(a)
        return None

def dbToJSON():
    conexion, cursor = generarConexionBBDD(DATABASE_USER, DATABASE_PASSWORD)

    try:
        # Consultar datos de la tabla de taxis
        cursor.execute("SELECT id, estado, sensores, posicion, cliente, destino, token FROM taxis")
        taxis = [
            {
                "id": row[0],
                "estado": row[1],
                "sensores": row[2],
                "posicion": row[3],
                "cliente": row[4],
                "destino": row[5],
                "token": row[6]
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

        enviarJSONEnTopic(json_data, TOPIC_ESTADOS_MAPA, BROKER_ADDR)

    except Exception as e:
        print(f"Error al convertir la base de datos a JSON: {e}")
        return None

    finally:
        # Cerrar la conexión a la base de datos
        conexion.close()

def comprobarTaxi(idTaxi, tokenTaxi):
    try:
        conexion, cursor = generarConexionBBDD(DATABASE_USER, DATABASE_PASSWORD)

        cursor.execute("SELECT token FROM taxis WHERE id = ?", (idTaxi,))
        resultado = cursor.fetchone()

        if resultado is None:
            printInfo(f"Taxi {idTaxi} no encontrado en la base de datos.")
            return False
        else:
            if idTaxi in taxisConectados:
                printInfo(f"Taxi {idTaxi} existe y ya está conectado.")
                return False
            else:
                if tokenTaxi == resultado[0]:
                    printInfo(f"Taxi {idTaxi} autenticado con éxito.")
                    return True
                else:
                    printError(f"Token incorrecto para el taxi {idTaxi}.")
                    return False
    except Exception as e:
        printError(e)
        return False

def gestionarBrokerClientes():
    global diccionarioLocalizaciones
    global taxisLibres, taxisConectados

    consumidor = conectarBrokerConsumidor(BROKER_ADDR, TOPIC_CLIENTES) # ,auto_offset_reset='earliest')

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
                ejecutarSentenciaBBDD(f"UPDATE clientes SET IP = '{mensaje.key.decode(FORMAT)}' WHERE id = '{idCliente}'")
                printDebug(f"Estado de los taxis (Conectados, Libres): {taxisConectados}, {taxisLibres}.")
                if len(taxisLibres) < 1:
                    printWarning(f"No hay taxis disponibles. Cancelando servicio a cliente {idCliente}.")
                    publicarMensajeEnTopic(f"[EC_Central->EC_Customer_{idCliente}][KO]", TOPIC_CLIENTES, BROKER_ADDR)
                else:
                    taxiElegido = taxisLibres.pop()
                    printInfo(f"Asignando servicio del cliente {idCliente} al taxi {taxiElegido}.")
                    mapa.activateTaxi(taxiElegido)
                    publicarMensajeEnTopic(f"[EC_Central->EC_DE_{taxiElegido}][SERVICIO][{idCliente}->{localizacion}]", TOPIC_TAXIS, BROKER_ADDR)

                    ejecutarSentenciaBBDD(f"UPDATE taxis SET estado = 'enCamino' WHERE id = {taxiElegido}")
                    ejecutarSentenciaBBDD(f"UPDATE taxis SET cliente = '{idCliente}' WHERE id = {taxiElegido}")
                    ejecutarSentenciaBBDD(f"UPDATE taxis SET destino = '{localizacion}' WHERE id = {taxiElegido}")

                    publicarMensajeEnTopic(f"[EC_DE_{taxiElegido}] Servicio asignado [{idCliente}->{localizacion}]", TOPIC_ERRORES_MAPA, BROKER_ADDR)
                    printInfo(f"[EC_DE_{taxiElegido}] Servicio asignado [{idCliente}->{localizacion}]")
                    printLog(taxiElegido, f"Servicio asignado [{idCliente}->{localizacion}]")
        else:
            #printInfo(mensaje)
            #printInfo(mensaje.value.decode(FORMAT))
            printError("Mensaje desconocido recibido en {TOPIC_CLIENTES} : {mensaje.value.decode(FORMAT)}.")
    #except kafka.errors.NoBrokersAvailable as error:
    #    printInfo("FATAL: No se ha podido conectar con el broker")
    #    printInfo(error)
    #    sys.exit()

def gestionarBrokerTaxis():
    global BROKER_ADDR, taxisLibres
    #TODO: try: except:
    consumidor = conectarBrokerConsumidor(BROKER_ADDR, TOPIC_TAXIS)

    for mensaje in consumidor:
        camposMensaje = re.findall('[^\[\]]+', mensaje.value.decode(FORMAT))
        print("DEBUG: ", camposMensaje)
        #printInfo(camposMensaje)
        #printInfo(mensaje)
        if camposMensaje[0].startswith("EC_Central"):
            #Nuestros propios mensajes
            pass
        elif camposMensaje[0].startswith("EC_DE"):
            idTaxi = camposMensaje[0].split("->")[0][6:]
            if camposMensaje[1] == "AUTH_REQUEST":
                pass #Aquí no nos importa
            elif camposMensaje[1] == "SENSORES":
                # ['EC_DE_1->EC_Central', 'SENSORES', 'OK']
                estado = camposMensaje[2]
                printInfo(f"Taxi {idTaxi} ha cambiado su estado a {estado}.")
                if estado == "OK":
                    mapa.activateTaxi(idTaxi)
                elif estado == "KO":
                    mapa.deactivateTaxi(idTaxi)

                ejecutarSentenciaBBDD(f"UPDATE taxis SET sensores = '{estado}' WHERE id = {idTaxi}")
                publicarMensajeEnTopic(f"[EC_DE_{idTaxi}] Cambio su estado a: {estado}", TOPIC_ERRORES_MAPA, BROKER_ADDR)
                printInfo(f"[EC_DE_{idTaxi}] Cambio su estado a: {estado}")
                printLog(idTaxi, f"Cambio su estado a: {estado}")

            elif camposMensaje[1] == "MOVIMIENTO":
                # ['EC_DigitalEngine-1->EC_Central', '(1,2)']
                posX = int(camposMensaje[2].split(",")[0])
                posY = int(camposMensaje[2].split(",")[1])
                printInfo(f"Movimiento ({posX},{posY}) recibido del taxi {idTaxi}.")
                ejecutarSentenciaBBDD(f"UPDATE taxis SET posicion = '{posX},{posY}' WHERE id = {idTaxi}")
                # Si el taxi tiene un cliente, moverlo también
                taxiBBDD = ejecutarSentenciaBBDD(f"SELECT * FROM taxis WHERE id = {idTaxi}")
                if taxiBBDD[0][1] == "servicio":
                    idCliente = taxiBBDD[0][4]
                    ejecutarSentenciaBBDD(f"UPDATE clientes SET posicion = '{posX},{posY}' WHERE id = '{idCliente}'")
                    mapa.move(f"cliente_{idCliente}", posX, posY)



                mapa.move(f"taxi_{idTaxi}", posX, posY)
                mapa.print()

                publicarMensajeEnTopic(f"[EC_Central->ALL][{mapa.exportJson()}][{mapa.exportActiveTaxis()}]", TOPIC_TAXIS, BROKER_ADDR)
            elif camposMensaje[1] == "SERVICIO":
                if camposMensaje[2] == "CLIENTE_RECOGIDO":
                    publicarMensajeEnTopic(f"EC_Central->EC_Customer_{camposMensaje[3]}[RECOGIDO]", TOPIC_CLIENTES, BROKER_ADDR)
                    ejecutarSentenciaBBDD(f"UPDATE taxis SET estado = 'servicio' WHERE id = {idTaxi}")
                    publicarMensajeEnTopic(f"[EC_DE_{idTaxi}] Recogido a su cliente {camposMensaje[3]}", TOPIC_ERRORES_MAPA, BROKER_ADDR)
                    printInfo(f"[EC_DE_{idTaxi}] Recogido a su cliente {camposMensaje[3]}")
                    printLog(idTaxi, f"Recogido a su cliente {camposMensaje[3]}")
                    #actualizarEstadosJSON(True, camposMensaje[3], f"OK. Taxi {idTaxi}", camposMensaje[4])
                    #actualizarEstadosJSON(False, idTaxi, f"OK. Servicio {camposMensaje[3]}", camposMensaje[4]) # TAXI

                if camposMensaje[2] == "CLIENTE_EN_DESTINO":
                    posX = int(camposMensaje[4].split(",")[0])
                    posY = int(camposMensaje[4].split(",")[1])
                    idCliente = camposMensaje[3]

                    publicarMensajeEnTopic(f"EC_Central->EC_Customer_{idCliente}[EN_DESTINO]", TOPIC_CLIENTES, BROKER_ADDR)

                    mapa.deactivateTaxi(idTaxi)
                    publicarMensajeEnTopic(f"[EC_DE_{idTaxi}] Llevado al cliente {camposMensaje[3]} a su destino", TOPIC_ERRORES_MAPA, BROKER_ADDR)
                    printInfo(f"[EC_DE_{idTaxi}] Llevado al cliente {camposMensaje[3]} a su destino")
                    printLog(idTaxi, f"Llevado al cliente {camposMensaje[3]} a su destino")
                    #actualizarEstadosJSON(True, camposMensaje[3], "OK. En destino", camposMensaje[4]) # CLIENTE
                    #actualizarEstadosJSON(False, idTaxi, "OK. Parado") # TAXI

                    taxisLibres.append(idTaxi)
                    ejecutarSentenciaBBDD(f"UPDATE taxis SET estado = 'esperando' WHERE id = {idTaxi}")
                    ejecutarSentenciaBBDD(f"UPDATE taxis SET cliente = NULL WHERE id = {idTaxi}")
                    ejecutarSentenciaBBDD(f"UPDATE taxis SET destino = NULL WHERE id = {idTaxi}")
        else:
            #printInfo(mensaje)
            #printInfo(mensaje.value.decode(FORMAT))
            printError(f"Mensaje desconocido recibido en {TOPIC_TAXIS} : {mensaje.value.decode(FORMAT)}.")


def autenticarTaxi(conexion, direccion):
    mensaje = recibirMensajeCliente(conexion)
    if mensaje is None:
        printWarning("Perdida conexión con un taxi durante la autentificación.")
        return -1

    camposMensaje = re.findall('[^\[\]]+', mensaje)
    idTaxi = camposMensaje[0].split("->")[0][6:]
    tokenTaxi = camposMensaje[6]
    if comprobarTaxi(idTaxi, tokenTaxi):
        ejecutarSentenciaBBDD(f"UPDATE taxis SET IP = '{direccion[0]}' WHERE id = {idTaxi}")
        ejecutarSentenciaBBDD(f"UPDATE taxis SET sensores = '{camposMensaje[2]}' WHERE id = {idTaxi}")
        if camposMensaje[3] != "None,None":
            printInfo(f"El taxi {idTaxi} tenía posición, por lo tanto nosotros habíamos caído.")
            # Si el taxi estaba realizando un servicio en el momento de nuestra caída comprobar si lo ha finalizado y notificar al cliente
            ejecutarSentenciaBBDD(f"UPDATE taxis SET posicion = '{camposMensaje[3].split(',')[0]},{camposMensaje[3].split(',')[1]}' WHERE id = {idTaxi}")
            mapa.setPosition(f"taxi_{idTaxi}", camposMensaje[3].split(',')[0], camposMensaje[3].split(',')[1])
            if camposMensaje[4] != None:
                mapa.activateTaxi(idTaxi)
                if camposMensaje[5] == "True":
                    ## El cliente ha sido recogido
                    ejecutarSentenciaBBDD(f"UPDATE clientes SET posicion = '{camposMensaje[3].split(',')[0]},{camposMensaje[3].split(',')[1]}' WHERE id = {camposMensaje[4]}")
                    mapa.setPosition(f"cliente_{camposMensaje[4]}", camposMensaje[3].split(',')[0], camposMensaje[3].split(',')[1])
                    ejecutarSentenciaBBDD(f"UPDATE taxis SET estado = 'servicio' WHERE id = {idTaxi}")
                else:
                    ejecutarSentenciaBBDD(f"UPDATE taxis SET estado = 'enCamino' WHERE id = {idTaxi}")
                taxisLibres.remove(idTaxi)
        else:
            printInfo(f"El taxi {idTaxi} acaba de arrancar.")
        #[EC_Central->EC_DE_1][AUTHORIZED][1,2][Cliente][Destino]
        taxiBBDD = ejecutarSentenciaBBDD(f"SELECT * FROM taxis WHERE id = {idTaxi}")

        enviarMensajeServidor(conexion, f"[EC_Central->EC_DE_{idTaxi}][AUTHORIZED][{taxiBBDD[0][3].split(',')[0]},{taxiBBDD[0][3].split(',')[1]}][{taxiBBDD[0][4]}][{taxiBBDD[0][5]}]")
        enviarMensajeServidor(conexion, f"[EC_Central->EC_DE_{idTaxi}][{mapa.exportJson()}][{mapa.exportActiveTaxis()}]")

        publicarMensajeEnTopic(f"[EC_DE_{idTaxi}] Autorizado.", TOPIC_ERRORES_MAPA, BROKER_ADDR)
        printInfo(f"[EC_DE_{idTaxi}] Autorizado.")
        printLog(idTaxi, f"Taxi {idTaxi} ha sido autorizado.")
        #actualizarEstadosJSON(False, idTaxi, "OK. Parado")
        return idTaxi

    else:
        enviarMensajeServidor(conexion, f"[EC_Central->EC_DE_{idTaxi}][NOT_AUTHORIZED]")
        return -1


def gestionarTaxi(conexion, direccion):
    global taxisConectados, taxisLibres
    idTaxi = autenticarTaxi(conexion, direccion)

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
            cliente = ejecutarSentenciaBBDD(f"SELECT cliente FROM taxis WHERE id = {idTaxi}")[0][0]
            printWarning(f"Cancelando servicio a cliente {cliente} por caída de su taxi.")
            publicarMensajeEnTopic(f"[EC_Central->EC_Customer_{cliente}][KO]", TOPIC_CLIENTES, BROKER_ADDR)
            ejecutarSentenciaBBDD(f"UPDATE taxis SET cliente = NULL WHERE id = {idTaxi}")
            ejecutarSentenciaBBDD(f"UPDATE taxis SET destino = NULL WHERE id = {idTaxi}")

        mapa.deactivateTaxi(idTaxi)
        ejecutarSentenciaBBDD(f"UPDATE taxis SET estado = 'desconectado' WHERE id = {idTaxi}")

        mapa.print()

        publicarMensajeEnTopic(f"[EC_DE_{idTaxi}] Su conexión ha caido.", TOPIC_ERRORES_MAPA, BROKER_ADDR)
        printInfo(f"[EC_DE_{idTaxi}] Su conexión ha caido.")
        printLog(idTaxi, "Su conexión ha caido.")

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
        if irBase != estado_anterior:
            if irBase:
                publicarMensajeEnTopic(f"[EC_Central->BASE][ALL][SI]", TOPIC_TAXIS, BROKER_ADDR)
                publicarMensajeEnTopic(f"[EC_Central] Enviando todos los taxis a base", TOPIC_ERRORES_MAPA, BROKER_ADDR)
                printInfo("Enviando todos los taxis a base.")
                printLog("ALL", "Enviando todos los taxis a base.")
            else:
                publicarMensajeEnTopic(f"[EC_Central->BASE][ALL][NO]", TOPIC_TAXIS, BROKER_ADDR)
                publicarMensajeEnTopic(f"[EC_Central] Los taxis pueden salir de base y continuar su servicio", TOPIC_ERRORES_MAPA, BROKER_ADDR)
                printInfo("Cancelando envío a base.")
                printLog("ALL", "Cancelando envío a base.")

            # Actualizamos el estado anterior
            estado_anterior = irBase
        time.sleep(1)

def dirigirTaxiABase(idTaxi):
    try:
        if idTaxi not in taxisConectados:
            printError(f"Taxi {idTaxi} no está conectado.")
            return

        if idTaxi in taxisEnBase:
            taxisEnBase.remove(idTaxi)
            publicarMensajeEnTopic(f"[EC_Central->BASE][{idTaxi}][NO]", TOPIC_TAXIS, BROKER_ADDR)
            publicarMensajeEnTopic(f"[EC_Central] Los taxis pueden salir de base y continuar su servicio", TOPIC_ERRORES_MAPA, BROKER_ADDR)
            printInfo(f"Cancelando envio a la base del taxi {idTaxi}.")
            printLog(idTaxi, "Cancelando envio a la base.")
        else:
            taxisEnBase.append(idTaxi)
            publicarMensajeEnTopic(f"[EC_Central->BASE][{idTaxi}][SI]", TOPIC_TAXIS, BROKER_ADDR)
            publicarMensajeEnTopic(f"[EC_Central] Enviando taxi {idTaxi} a base", TOPIC_ERRORES_MAPA, BROKER_ADDR)
            printInfo(f"Enviando taxi {idTaxi} a la base.")
            printLog(idTaxi, "Enviando a la base.")
    except Exception as e:
        raise e


def inputBase():
    global irBase

    threading.Thread(target=dirigirABaseATodos).start()

    while True:
        user_input = input("\033[94mIntroduce 'ALL' para enviar todos los taxis a base o un ID específico: \033[0m\n").strip()

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
    IP = "http://localhost:5002/consultarClima"


    while True:
        try:
            response = requests.get(IP)
            printLog("CENTRAL", "Petición para consultar clima.")
            printInfo("Petición para consultar clima.")
            if response.status_code == 200:
                data = response.json()
                if data["status"] == "KO":
                    climaAdverso = True
                    printWarning(data["message"])
                else:
                    climaAdverso = False
                    printInfo(data["message"])

                printLog("CENTRAL", data["message"])
            else:
                printError("Error al consultar el clima")
                printLog("CENTRAL", "Error al consultar el clima")
        except Exception as e:
            printError(f"Error al verificar el clima: {e}")
            printLog("CENTRAL", f"Error al verificar el clima: {e}")
        finally:
            time.sleep(10)

### API
@app.route('/estadoActual-mapa', methods=['GET'])
def estadoActual():
    return mapa.exportJson()

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

    ##hiloApi = threading.Thread(target=app.run, kwargs={'debug': True})
    ##hiloApi.start()

    # Iniciar el hilo para verificar el clima
    hiloClima = threading.Thread(target=verificarClima)
    hiloClima.start()

if __name__ == "__main__":
    # Ejecuta el servidor Flask en un hilo separado
    hiloApi = threading.Thread(target=app.run, kwargs={'debug': True, 'use_reloader': False})
    hiloApi.start()

    # Llama al resto de tu lógica principal
    main()
