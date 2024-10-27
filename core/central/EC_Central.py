import sys
import time
import json
import re
import sqlite3
import socket
import threading
from kafka import KafkaConsumer, KafkaProducer

sys.path.append('../../shared')
from EC_Shared import *
from EC_Map import Map
from EC_Map import iniciarMapa

HOST = "" # Simbólico, nos permite escuchar en todas las interfaces de red
LISTEN_PORT = None
THIS_ADDR = None
BROKER_IP = None
BROKER_PORT = None
BROKER_ADDR = None

diccionarioLocalizaciones = {}
taxisConectados = [] # [1, 2, 3, 5]
taxisLibres = [] # [2, 3]
mapa = Map()

def     comprobarArgumentos(argumentos):
    if len(argumentos) != 4:
        printInfo("CHECKS: ERROR LOS ARGUMENTOS. Necesito estos argumentos: <LISTEN_PORT> <BROKER_IP> <BROKER_PORT>")
        exit()
    printInfo("Número de argumentos correcto.")

def asignarConstantes(argumentos):
    # Asignamos las constantes
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
        with open('./EC_locations.json') as json_file:
            jsonLocalizaciones = json.load(json_file)
            for key in jsonLocalizaciones:
                value = jsonLocalizaciones[key]
                for item in value:
                    diccionarioLocalizaciones.update({item['Id'] : item['POS']})
                    printInfo(f"Cargada localización {item['Id']} con coordenadas ({item['POS']}).")

            #printInfo(diccionarioLocalizaciones)
            printInfo("Mapa cargado con éxito.")
    except IOError as error:
        printInfo("FATAL: No se ha podido abrir el fichero.")
        sys.exit()

    #TODO: JSON FILE DEL ULTIMO ESTADO DE LOS TAXIS
    mapa.diccionarioPosiciones.update({"taxi_1" : "2,3"})
    mapa.diccionarioPosiciones.update({"taxi_2" : "8,2"})
    mapa.diccionarioPosiciones.update({"taxi_3": "10,4"})
    mapa.diccionarioPosiciones.update({"cliente_d" : "3,5"})
    mapa.diccionarioPosiciones.update({"cliente_e" : "7,8"})
    mapa.diccionarioPosiciones.update({"localizacion_A" : "9,15"})
    mapa.diccionarioPosiciones.update({"localizacion_C" : "14,7"})

def iniciarBBDD():
    conexionBBDD = sqlite3.connect('database.db')
    cursor = conexionBBDD.cursor()

    fd = open('crearBBDD.sql', 'r')
    sqlFile = fd.read()
    fd.close()

    sqlCommands = sqlFile.split(';')
    for command in sqlCommands:
        try:
            cursor.execute(command)
        except OperationalError as msg:
            printInfo("Command skipped: ", msg)

    printInfo("Base de datos preparada.")

def gestionarBrokerClientes():
    global BROKER_ADDR
    global taxisLibres, taxisConectados

    printInfo(f"Conectando al broker en la dirección ({BROKER_ADDR}) como consumidor CLIENTES.")
    #TODO: try:
    consumidor = KafkaConsumer(TOPIC_CLIENTES,bootstrap_servers=BROKER_ADDR) # ,auto_offset_reset='earliest')

    for mensaje in consumidor:
        camposMensaje = re.findall('[^\[\]]+', mensaje.value.decode(FORMAT))
        #printInfo(camposMensaje)
        #printInfo(mensaje)
        if camposMensaje[0].startswith("EC_Central"):
            #Nuestros propios mensajes
            pass
        elif camposMensaje[0].startswith("EC_Customer"):
            # ['EC_Customer_a->EC_Central', 'E']
            time.sleep(0.5) # Evitar que se termine el servicio antes de que el cliente lo pueda leer !!necesario
            idCliente = camposMensaje[0].split("->")[0][12:]
            localizacion = camposMensaje[1]
            printInfo(f"Solicitud de servicio recibida, cliente {idCliente}, destino {localizacion}.")
            global diccionarioLocalizaciones
            if localizacion not in diccionarioLocalizaciones:
                printInfo(f"ERROR: La localización {localizacion} no existe. Cancelando servicio a cliente {idCliente}")
                publicarMensajeEnTopic("[EC_Central->EC_Customer_{idCliente}][KO]", TOPIC_CLIENTES, BROKER_ADDR)
            else:
                printInfo(f"Estado de los taxis (L, C): {taxisLibres},  {taxisConectados}")
                if len(taxisLibres) > 0:
                    taxiElegido = taxisLibres.pop()
                    printInfo(f"Asignando servicio del cliente {idCliente} al taxi {taxiElegido}.")
                    publicarMensajeEnTopic(f"[EC_Central->EC_DE_{taxiElegido}][SERVICIO][{idCliente}->{localizacion}]", TOPIC_TAXIS, BROKER_ADDR)
                else:
                    printInfo(f"ERROR: No hay taxis disponibles para el cliente {idCliente}.")
                    publicarMensajeEnTopic(f"[EC_Central->EC_Customer_{idCliente}][KO]", TOPIC_CLIENTES, BROKER_ADDR)

        else:
            #printInfo(mensaje)
            #printInfo(mensaje.value.decode(FORMAT))
            printInfo(f"ERROR: Mensaje desconocido recibido en {TOPIC_CLIENTES} : {mensaje.value.decode(FORMAT)}.")
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
        #printInfo(camposMensaje)
        #printInfo(mensaje)
        if camposMensaje[0].startswith("EC_Central"):
            #Nuestros propios mensajes
            pass
        elif camposMensaje[0].startswith("EC_DE"):
            idTaxi = camposMensaje[0].split("->")[0][6:]
            if camposMensaje[1] == "AUTH_REQUEST":
                pass #Aquí no nos importa
            elif camposMensaje[1] == "ESTADO":
                # ['EC_DE_1->EC_Central', 'ESTADO', 'OK']
                estado = camposMensaje[2]
                printInfo(f"Taxi {idTaxi} ha cambiado su estado a {estado}.")
                if estado == "OK":
                    mapa.activateTaxi(idTaxi)
                elif estado == "KO":
                    mapa.deactivateTaxi(idTaxi)
            elif camposMensaje[1] == "MOVIMIENTO":
                # ['EC_DigitalEngine-1->EC_Central', '(1,2)']
                posX = int(camposMensaje[2].split(",")[0])
                posY = int(camposMensaje[2].split(",")[1])
                printInfo(f"Movimiento ({posX},{posY}) recibido del taxi {idTaxi}.")
                if camposMensaje[3] != "None":
                    mapa.move(f"cliente_{camposMensaje[3]}", posX, posY)
                mapa.move(f"taxi_{idTaxi}", posX, posY)
                mapa.print()
                mapa.draw_on_canvas()
                publicarMensajeEnTopic(f"[EC_Central->ALL][{mapa.exportJson()}][{mapa.exportActiveTaxis()}]", TOPIC_TAXIS, BROKER_ADDR)
            elif camposMensaje[1] == "SERVICIO":
                if camposMensaje[2] == "CLIENTE_RECOGIDO":
                    publicarMensajeEnTopic(f"EC_Central->EC_Customer_{camposMensaje[3]}[RECOGIDO]", TOPIC_CLIENTES, BROKER_ADDR)
                    mapa.move(f"cliente_{camposMensaje[3]}", 0, 0)
                    mapa.print()
                    publicarMensajeEnTopic(f"[EC_Central->ALL][{mapa.exportJson()}][{mapa.exportActiveTaxis()}]", TOPIC_TAXIS, BROKER_ADDR)

                if camposMensaje[2] == "CLIENTE_EN_DESTINO":
                    posX = int(camposMensaje[4].split(",")[0])
                    posY = int(camposMensaje[4].split(",")[1])
                    idCliente = camposMensaje[3]
                    mapa.move(f"cliente_{idCliente}", posX, posY)
                    mapa.print()
                    publicarMensajeEnTopic(f"[EC_Central->ALL][{mapa.exportJson()}][{mapa.exportActiveTaxis()}]", TOPIC_TAXIS, BROKER_ADDR)
    
                    publicarMensajeEnTopic(f"EC_Central->EC_Customer_{idCliente}[EN_DESTINO]", TOPIC_CLIENTES, BROKER_ADDR)
                    taxisLibres.append(idTaxi)
        else:
            #printInfo(mensaje)
            #printInfo(mensaje.value.decode(FORMAT))
            printInfo(f"ERROR: Mensaje desconocido recibido en {TOPIC_TAXIS} : {mensaje.value.decode(FORMAT)}.")
    #except kafka.errors.NoBrokersAvailable as error:
    #    printInfo("FATAL: No se ha podido conectar con el broker")
    #    printInfo(error)
    #    sys.exit()

# Devuelve id del taxi o -1 si no autentifica
def autenticarTaxi(conexion, direccion):
    try:
        longitud_mensaje = conexion.recv(HEADER).decode(FORMAT)
        if longitud_mensaje:
            longitud_mensaje = int(longitud_mensaje)
            mensaje = conexion.recv(longitud_mensaje).decode(FORMAT)
            printInfo(f"He recibido del cliente {direccion} el mensaje: {mensaje}")
            idTaxi = mensaje[7:8]
            if True: #COMPROBAR BASE DE DATOS Y VER SI YA HAY UNO CONECTADO
                printInfo("El taxi existe y no está conectado")
                try:
                    posicion = mapa.getPosition(f"taxi_{idTaxi}")

                    enviarMensajeServidor(conexion, f"[EC_Central->EC_DE_{idTaxi}][AUTHORIZED][{posicion.split(',')[0]},{posicion.split(',')[1]}]")
                    # SE PUEDE HACER POR KAFKA TAMBIEN
                    enviarMensajeServidor(conexion, f"[EC_Central->EC_DE_{idTaxi}][{mapa.exportJson()}][{mapa.exportActiveTaxis()}]")
                except:
                    printInfo("ERROR: Taxi no encontrado en el mapa")
            else:
                printInfo("El taxi no existe o está conectado")
                enviarMensajeServidor(conexion, f"[EC_Central->EC_DE_{idTaxi}][NOT_AUTHORIZED]")
                return -1
        else:
            printInfo(f"ERROR: MENSAJE VACIO, CONEXION PERDIDA.")
            return -1
    except Exception as e:
        printInfo(f"ERROR: EXCEPCION, CONEXION PERDIDA: {e}")

    return idTaxi


def gestionarTaxi(conexion, direccion):
    global taxisConectados, taxisLibres
    idTaxi = autenticarTaxi(conexion, direccion)

    if idTaxi != -1:
        taxisConectados.append(idTaxi)
        taxisLibres.append(idTaxi)
        #Añadir taxi disponible a la bbdd
        #conexionBBDD = sqlite3.connect('database.db')
        #cursor = conexionBBDD.cursor()
        #cursor.execute("UPDATE taxis SET estado = 'conectado' WHERE id = ?", (direccion,))
        #printInfo("Taxi con conexion {0} y {1} autorizado.".format(conexion, direccion))

        #Monitorizar socket
        while True:
            try:
                mensaje = recibirMensajeServidor(conexion)
                if mensaje == None:
                    printInfo(f"Conexión con el taxi ?? {direccion} perdida.")
                    printInfo(f"ERROR TAXI: MENSAJE VACIO, CONEXION PERDIDA.")
                    break
                else:
                    printInfo(f"Mensaje del taxi {direccion} recibido: {mensaje}")
                    printInfo(f"ERROR: MENSAJE DESCONOCIDO: {mensaje}")
            except Exception as e:
                printInfo(f"ERROR: EXCEPCION, CONEXION PERDIDA: {e}")

        #Taxi ha caido
        printInfo(f"Taxi con id {idTaxi}, conexión {conexion} y {direccion} ha caido.")
        taxisConectados.remove(idTaxi)
        taxisLibres.remove(idTaxi)
        mapa.deactivateTaxi(f"taxi_{idTaxi}")
    else:
        printInfo(f"Taxi con conexion {conexion} y {direccion} no autorizado. Desconectando...")
        conexion.close()

def asignarServicio(taxi, cliente, localizacion):
    time.sleep(0.5) # Evitar que se termine el servicio antes de que el cliente lo pueda leer
    printInfo(f"Servicio  {cliente}, {localizacion} finalizado por {taxi}")

    publicarMensajeEnTopic(f"EC_Central->EC_Customer_{cliente}[OK]", TOPIC_CLIENTES, BROKER_ADDR)

    global taxisLibres
    taxisLibres.append(taxi)

def main():
    comprobarArgumentos(sys.argv)
    asignarConstantes(sys.argv)
    leerConfiguracionMapa()

    #TODO: Popular base de datos en arranque o ver si habíamos crasheado
    iniciarBBDD()

    hiloClientes = threading.Thread(target=gestionarBrokerClientes)
    hiloClientes.start()

    hiloTaxis = threading.Thread(target=gestionarBrokerTaxis)
    hiloTaxis.start()

    # Autentificaciones y saber si taxi cae
    socketEscucha = abrirSocketServidor(THIS_ADDR)
    socketEscucha.listen()

    hiloMapa = threading.Thread(target=iniciarMapa)
    hiloMapa.start()

    while True:
        #printInfo("acabo de iterar")
        conexion, direccion = socketEscucha.accept()
        hiloTaxi = threading.Thread(target=gestionarTaxi, args=(conexion, direccion))
        hiloTaxi.start()

if __name__ == "__main__":
    main()
