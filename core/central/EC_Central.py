import sys
import time
import json
import re
import sqlite3
from sqlite3 import OperationalError
import socket
import threading
from kafka import KafkaConsumer, KafkaProducer

sys.path.append('../../shared')
from EC_Shared import *
from EC_Map import Map
from EC_Map import iniciarMapa

DATABASE = './resources/database.db'

HOST = "" # Simbólico, nos permite escuchar en todas las interfaces de red
LISTEN_PORT = None
THIS_ADDR = None
BROKER_IP = None
BROKER_PORT = None
BROKER_ADDR = None

taxisConectados = [] # [1, 2, 3, 5]
taxisLibres = [] # [2, 3]
mapa = Map()
irBase = False

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
        printInfo("FATAL: No se ha podido abrir el fichero.")
        sys.exit()

def leerBBDD():
    conexionBBDD = sqlite3.connect(DATABASE)
    cursor = conexionBBDD.cursor()

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
    conexionBBDD.close()

def ejecutarSentenciaBBDD(sentencia):
    printInfo(f"Ejecutando sentencia en la base de datos: '{sentencia}'.")
    try:
        conexionBBDD = sqlite3.connect(DATABASE)
        cursor = conexionBBDD.cursor()
        cursor.execute(sentencia)
        resultado = cursor.fetchall()
        conexionBBDD.commit()
        conexionBBDD.close()
        dbToJSON()
        return resultado
    except Exception as a:
        printError(a)
        return None
    
def dbToJSON():
    # Conexión a la base de datos SQLite
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

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
        
        enviarJSONEnTopic(json_data, TOPIC_ESTADOS_MAPA, BROKER_ADDR)

    except Exception as e:
        print(f"Error al convertir la base de datos a JSON: {e}")
        return None

    finally:
        # Cerrar la conexión a la base de datos
        conn.close()

def comprobarTaxi(idTaxi):
    try:
        conexionBBDD = sqlite3.connect(DATABASE)
        cursor = conexionBBDD.cursor()

        cursor.execute("SELECT id FROM taxis WHERE id = ?", (idTaxi,))
        if cursor.fetchone() == None:
            printInfo(f"Taxi {idTaxi} no encontrado en la base de datos.")
            return False
        else:
            if idTaxi in taxisConectados:
                printInfo(f"Taxi {idTaxi} existe y ya está conectado.")
                return False
            else:
                printInfo(f"Taxi {idTaxi} existe y no está conectado.")
            return True
    except sqlite3.OperationalError as msg:
        printError(msg)
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
                    #actualizarEstadosJSON(True, camposMensaje[3], f"OK. Taxi {idTaxi}", camposMensaje[4])
                    #actualizarEstadosJSON(False, idTaxi, f"OK. Servicio {camposMensaje[3]}", camposMensaje[4]) # TAXI

                if camposMensaje[2] == "CLIENTE_EN_DESTINO":
                    posX = int(camposMensaje[4].split(",")[0])
                    posY = int(camposMensaje[4].split(",")[1])
                    idCliente = camposMensaje[3]

                    publicarMensajeEnTopic(f"EC_Central->EC_Customer_{idCliente}[EN_DESTINO]", TOPIC_CLIENTES, BROKER_ADDR)

                    mapa.deactivateTaxi(idTaxi)
                    publicarMensajeEnTopic(f"[EC_DE_{idTaxi}] Llevado al cliente {camposMensaje[3]} a su destino", TOPIC_ERRORES_MAPA, BROKER_ADDR)
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
    if comprobarTaxi(idTaxi):
        ejecutarSentenciaBBDD(f"UPDATE taxis SET sensores = '{camposMensaje[2]}' WHERE id = {idTaxi}")
        if camposMensaje[3] != "None,None":
            printInfo(f"El taxi {idTaxi} tenía posición, por lo tanto nosotros habíamos caído.")
            # Si el taxi estaba realizando un servicio en el momento de nuestra caída comprobar si lo ha finalizado y notificar al cliente
            ejecutarSentenciaBBDD(f"UPDATE taxis SET posicion = '{camposMensaje[3].split(',')[0]},{camposMensaje[3].split(',')[1]}' WHERE id = {idTaxi}")
            mapa.setPosition(f"taxi_{idTaxi}", camposMensaje[3].split(',')[0], camposMensaje[3].split(',')[1])
            if camposMensaje[4] != None:
                mapa.activateTaxi(idTaxi)
                if camposMensaje[5] == "True":
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
            except:
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

def dirijirABase():
    global irBase

    estado_anterior = None 

    while True:
        if irBase != estado_anterior: 
            if irBase:
                printInfo("Enviando todos los taxis a base.")
                publicarMensajeEnTopic(f"[EC_Central->BASE][SI]", TOPIC_TAXIS, BROKER_ADDR)
                publicarMensajeEnTopic(f"[EC_Central] Enviando todos los taxis a base", TOPIC_ERRORES_MAPA, BROKER_ADDR)
            else:
                printInfo("Cancelando envío a base.")
                publicarMensajeEnTopic(f"[EC_Central->BASE][NO]", TOPIC_TAXIS, BROKER_ADDR)
                publicarMensajeEnTopic(f"[EC_Central] Los taxis pueden salir de base y continuar su servicio", TOPIC_ERRORES_MAPA, BROKER_ADDR)

            # Actualizamos el estado anterior
            estado_anterior = irBase

        

        time.sleep(1)

def inputBase():
    global irBase

    threading.Thread(target=dirijirABase).start()

    while True:
        if not irBase:
            input("Presiona Enter para enviar todos los taxis a base.")
            irBase = True
        else:
            input("Presiona Enter para cancelar el envío a base.")
            irBase = False

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

    hiloMapa = threading.Thread(target=iniciarMapa, args=(mapa, BROKER_ADDR,))
    hiloMapa.start()

    hiloBase = threading.Thread(target=inputBase)
    hiloBase.start()


if __name__ == "__main__":
    main()