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

def comprobarArgumentos(argumentos):
    if len(argumentos) != 4:
        print("CHECKS: ERROR LOS ARGUMENTOS. Necesito estos argumentos: <LISTEN_PORT> <BROKER_IP> <BROKER_PORT>")
        exit()
    print("INFO: Número de argumentos correcto.")

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
    print("INFO: Constantes asignadas.")

def leerConfiguracionMapa():
    global diccionarioLocalizaciones
    try:
        with open('./EC_locations.json') as json_file:
            jsonLocalizaciones = json.load(json_file)
            for key in jsonLocalizaciones:
                value = jsonLocalizaciones[key]
                for item in value:
                    print(f"INFO: Cargada localización {item['Id']} con coordenadas ({item['POS']}).")
                    diccionarioLocalizaciones.update({item['Id'] : item['POS']})

            #print(diccionarioLocalizaciones)
            print("INFO: Mapa cargado con éxito.")
    except IOError as error:
        print("FATAL: No se ha podido abrir el fichero.")
        sys.exit()

    #TODO: JSON FILE DEL ULTIMO ESTADO DE LOS TAXIS
    mapa.diccionarioPosiciones.update({"taxi_1" : "2,3"})
    mapa.taxisActivos = ["taxi_1"]
    mapa.diccionarioPosiciones.update({"taxi_2" : "8,2"})
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
            print("Command skipped: ", msg)

    print("INFO: Base de datos preparada.")

def gestionarBrokerClientes():
    global BROKER_ADDR
    print(f"INFO: Conectando al broker en la dirección ({BROKER_ADDR}) como consumidor CLIENTES.")
    #TODO: try:
    consumidor = KafkaConsumer(TOPIC_CLIENTES,bootstrap_servers=BROKER_ADDR) # ,auto_offset_reset='earliest')

    for mensaje in consumidor:
        camposMensaje = re.findall('[^\[\]]+', mensaje.value.decode(FORMAT))
        print(camposMensaje)
        #print(mensaje)
        if camposMensaje[0].startswith("EC_Central"):
            #Nuestros propios mensajes
            pass
        elif camposMensaje[0].startswith("EC_Customer"):
            # ['EC_Customer_a->EC_Central', 'E']
            idCliente = camposMensaje[0].split("->")[0][12:]
            localizacion = camposMensaje[1]
            print(f"INFO: Solicitud de servicio recibida, cliente {idCliente}, destino {localizacion}.")

            global diccionarioLocalizaciones
            if localizacion not in diccionarioLocalizaciones:
                print(f"ERROR: La localización {localizacion} no existe. Cancelando servicio a cliente {idCliente}")
                publicarMensaje("EC_Central->EC_Customer_{idCliente}[KO]", TOPIC_CLIENTES)
            else:
                global nuevoTaxisLibres
                if len(nuevoTaxisLibres) > 0:
                    taxiElegido = nuevoTaxisLibres.pop()
                    print(f"INFO: Asignando servicio del cliente {idCliente} al taxi {taxiElegido}.")
                    asignarServicio(taxiElegido, idCliente, localizacion)
        else:
            #print(mensaje)
            #print(mensaje.value.decode(FORMAT))
            print(f"ERROR: Mensaje desconocido recibido en {TOPIC_CLIENTES} : {mensaje.value.decode(FORMAT)}.")
    #except kafka.errors.NoBrokersAvailable as error:
    #    print("FATAL: No se ha podido conectar con el broker")
    #    print(error)
    #    sys.exit()

def gestionarBrokerTaxis():
    global BROKER_ADDR
    #TODO: try: except:
    consumidor = conectarBrokerConsumidor(BROKER_ADDR, TOPIC_TAXIS)

    for mensaje in consumidor:
        camposMensaje = re.findall('[^\[\]]+', mensaje.value.decode(FORMAT))
        #print(camposMensaje)
        #print(mensaje)
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
                print(f"INFO: Taxi {idTaxi} ha cambiado su estado a {estado}.")
                if estado == "OK":
                    mapa.taxisActivos.append(f"taxi_{idTaxi}")
                elif estado == "KO":
                    mapa.taxisActivos.remove(f"taxi_{idTaxi}")
            elif camposMensaje[1] == "MOVIMIENTO":
                # ['EC_DigitalEngine-1->EC_Central', '(1,2)']
                posX = int(camposMensaje[2].split(",")[0])
                posY = int(camposMensaje[2].split(",")[1])
                print(f"INFO: Movimiento ({posX},{posY}) recibido del taxi {idTaxi}.")
                mapa.move(f"taxi_{idTaxi}", posX, posY)
                mapa.print()
                publicarMensajeEnTopic(f"[EC_Central->ALL][{mapa.exportJson()}][{mapa.exportActiveTaxis}]", TOPIC_TAXIS, BROKER_ADDR)

        else:
            #print(mensaje)
            #print(mensaje.value.decode(FORMAT))
            print(f"ERROR: Mensaje desconocido recibido en {TOPIC_TAXIS} : {mensaje.value.decode(FORMAT)}.")
    #except kafka.errors.NoBrokersAvailable as error:
    #    print("FATAL: No se ha podido conectar con el broker")
    #    print(error)
    #    sys.exit()

# Devuelve id del taxi o -1 si no autentifica
def autenticarTaxi(conexion, direccion):
    while True:
        try:
            longitud_mensaje = conexion.recv(HEADER).decode(FORMAT)
            if longitud_mensaje:
                longitud_mensaje = int(longitud_mensaje)
                mensaje = conexion.recv(longitud_mensaje).decode(FORMAT)
                print(f"INFO: He recibido del cliente {direccion} el mensaje: {mensaje}")
                idTaxi = mensaje[7:8]
                if True: #COMPROBAR BASE DE DATOS Y VER SI YA HAY UNO CONECTADO
                    print("INFO: El taxi existe y no está conectado")
                    try:
                        posicion = mapa.getPosition(f"taxi_{idTaxi}")

                        enviarMensajeServidor(conexion, f"[EC_Central->EC_DE_{idTaxi}][AUTHORIZED][{posicion.split(',')[0]},{posicion.split(',')[1]}]")
                        # SE PUEDE HACER POR KAFKA TAMBIEN
                        enviarMensajeServidor(conexion, f"[EC_Central->ALL][{mapa.exportJson()}][{mapa.exportActiveTaxis()}]")
                    except:
                        print("ERROR: Taxi no encontrado en el mapa")
                else:
                    print("INFO: El taxi no existe o está conectado")
                    enviarMensajeServidor(conexion, f"[EC_Central->EC_DE_{idTaxi}][NOT_AUTHORIZED]")
                    return -1
            else:
                print(f"ERROR: MENSAJE VACIO, CONEXION PERDIDA.")
                break
        except Exception as e:
            print(f"ERROR: EXCEPCION, CONEXION PERDIDA: {e}")
    return idTaxi


def gestionarTaxi(conexion, direccion):
    idTaxi = autenticarTaxi(conexion, direccion)

    if idTaxi != -1:
        taxisConectados.append(idTaxi)
        taxisLibres.append(idTaxi)
        #Añadir taxi disponible a la bbdd
        #conexionBBDD = sqlite3.connect('database.db')
        #cursor = conexionBBDD.cursor()
        #cursor.execute("UPDATE taxis SET estado = 'conectado' WHERE id = ?", (direccion,))
        #print("INFO: Taxi con conexion {0} y {1} autorizado.".format(conexion, direccion))

        #Monitorizar socket
        while True:
            try:
                mensaje = recibirMensajeServidor(conexion)
                if mensaje == None:
                    print(f"INFO: Conexión con el taxi ?? {direccion} perdida.")
                    print(f"ERROR: MENSAJE VACIO, CONEXION PERDIDA.")
                    break
                else:
                    print(f"INFO: Mensaje del taxi {direccion} recibido: {mensaje}")
                    print(f"ERROR: MENSAJE DESCONOCIDO: {mensaje}")
            except Exception as e:
                print(f"ERROR: EXCEPCION, CONEXION PERDIDA: {e}")

        #Taxi ha caido
        print(f"INFO: Taxi con id {idTaxi}, conexión {conexion} y {direccion} ha caido.")
        nuevoTaxisConectados.remove(idTaxi)
        nuevoTaxisLibres.remove(idTaxi)
    else:
        print(f"INFO: Taxi con conexion {conexion} y {direccion} no autorizado. Desconectando...")
        conexion.close()

def asignarServicio(taxi, cliente, localizacion):
    time.sleep(0.5) # Evitar que se termine el servicio antes de que el cliente lo pueda leer
    # El cliente nos importa?
    # Donde está el cliente?
    print(f"INFO: Servicio  {cliente}, {localizacion} finalizado por {taxi}")
    publicarMensaje(f"EC_Central->EC_Customer_{cliente}[OK]", TOPIC_CLIENTES)

    global nuevoTaxisLibres
    nuevoTaxisLibres.append(taxi)

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
    while True:
        #print("acabo de iterar")
        conexion, direccion = socketEscucha.accept()
        hiloTaxi = threading.Thread(target=gestionarTaxi, args=(conexion, direccion))
        hiloTaxi.start()

if __name__ == "__main__":
    main()
