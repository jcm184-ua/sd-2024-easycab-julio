import sys
import time
import json
import re
import sqlite3
import socket
import threading
from kafka import KafkaConsumer, KafkaProducer

HEADER = 64
FORMAT = 'utf-8'

HOST = "" # Simbólico, nos permite escuchar en todas las interfaces de red
LISTEN_PORT = None
THIS_ADDR = None
BROKER_IP = None
BROKER_PORT = None
BROKER_ADDR = None
TOPIC_CLIENTES = 'CLIENTES'
TOPIC_TAXIS = 'TAXIS'

diccionarioLocalizaciones = {}
taxisConectados = 0
taxisLibres = 0
nuevoTaxisConectados = [1, 2, 3, 5]
nuevoTaxisLibres = [2, 3]

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
    print("INFO: Constantes asignadas")

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

def abrirSocket():
    global THIS_ADDR
    #print("INFO: Abriendo socket de escucha en el puerto {0}.".format(LISTEN_PORT))
    print(f"INFO: Abriendo socket de escucha en la dirección {THIS_ADDR}.")
    socketAbierto = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    socketAbierto.bind(THIS_ADDR)
    return socketAbierto

def publicarMensaje(mensaje, topic):
    global BROKER_ADDR
    print(f"INFO: Conectando al broker en la dirección ({BROKER_ADDR}) como productor.")
    conexion = KafkaProducer(bootstrap_servers=BROKER_ADDR)
    conexion.send(topic,(mensaje.encode(FORMAT)))
    print(f"INFO: Mensaje {mensaje} publicado.")
    # TODO: Fallo de publicación.
    conexion.close()
    print("INFO: Desconectado del broker como productor.")

def gestionarClientes():
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
            # ['EC_Customer-a->EC_Central', 'E']
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

def gestionarTaxis():
    global BROKER_ADDR
    print(f"INFO: Conectando al broker en la dirección ({BROKER_ADDR}) como consumidor TAXIS.")
    #TODO: try:
    consumidor = KafkaConsumer(TOPIC_TAXIS,bootstrap_servers=BROKER_ADDR) # ,auto_offset_reset='earliest')

    for mensaje in consumidor:
        camposMensaje = re.findall('[^\[\]]+', mensaje.value.decode(FORMAT))
        print(camposMensaje)
        #print(mensaje)
        if camposMensaje[0].startswith("EC_Central"):
            #Nuestros propios mensajes
            pass
        elif camposMensaje[0].startswith("EC_DigitalEngine"):
            # ['EC_DigitalEngine-1->EC_Central', '(1,2)']
            idTaxi = camposMensaje[0].split("->")[0][17:]
            posX = camposMensaje[1].split(",")[0][1:]
            posY = camposMensaje[1].split(",")[1][:1]
            print(f"INFO: Posición ({posX},{posY}) recibida del taxi {idTaxi}.")
            # TODO: Actualizar el mapa de todos los taxis
        else:
            #print(mensaje)
            #print(mensaje.value.decode(FORMAT))
            print(f"ERROR: Mensaje desconocido recibido en {TOPIC_TAXIS} : {mensaje.value.decode(FORMAT)}.")
    #except kafka.errors.NoBrokersAvailable as error:
    #    print("FATAL: No se ha podido conectar con el broker")
    #    print(error)
    #    sys.exit()

def modificarTaxisConectados(cambio):
    global taxisConectados
    taxisConectados = taxisConectados + cambio
    print("INFO: Número de taxis conectados actualizado: {0}".format(taxisConectados))

def modificarTaxisLibres(cambio):
    global taxisLibres
    taxisLibres = taxisLibres + cambio
    print("INFO: Número de taxis libres actualizado: {0}".format(taxisLibres))

def autenticarTaxi(conexion, direccion):
    #El taxi mandará su id, consultaremos la bbdd, si aparece y no estuviera ya conectado
    return True

def gestionarTaxi(conexion, direccion):
    if autenticarTaxi(conexion, direccion):
        # TODO: RECIBIR ID Y AÑADIRLO A LA LISTA
        modificarTaxisConectados(+1)
        modificarTaxisLibres(1)
        #Añadir taxi disponible a la bbdd
        conexionBBDD = sqlite3.connect('taxis.db')
        cursor = conexionBBDD.cursor()
        cursor.execute("UPDATE taxis SET estado = 'conectado' WHERE id = ?", (direccion,))
        print("INFO: Taxi con conexion {0} y {1} autorizado.".format(conexion, direccion))


        while True:
            msg_length = conexion.recv(HEADER).decode(FORMAT)
            if msg_length:
                msg_length = int(msg_length)
                msg = conexion.recv(msg_length).decode(FORMAT)
                print("MENSAJE RECIBIDO: {0}".format(msg))
            else:
                # El socket se ha desconectado
                print("ERROR: SOCKET {0} DESCONECTADO".format(direccion))
                # Cambiar a desconectado en la BBDD
                modificarTaxisLibres(-1)
                modificarTaxisConectados(-1)
                break
    else:
        print("INFO: Taxi con conexion {0} y {1} no autorizado. Desconectando..."
            .format(conexion, direccion))
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

    socketEscucha = abrirSocket()
    socketEscucha.listen()

    print("INFO: Entrando al bucle de ejecución...")

    # Crear hilo que se encarga de leer peticiones de clientes y les asigna su taxi.
        # dentro: ocurre una llamada de un cliente
    # if taxisLibres > 0:
    #     modificarTaxisLibres(-1)
    #    iniciarServicio()
    # else:
        #denegar servicio
        #print("CENTRAL: Denegado servicio a cliente n($id) por falta de taxis.")

    hiloClientes = threading.Thread(target=gestionarClientes)
    hiloClientes.start()
    hiloTaxis = threading.Thread(target=gestionarTaxis)
    hiloTaxis.start()

    #hiloTaxis = threading.Thread(target=gestionarTaxis)

    # Hacer un hilo que gestione la cola de los clientes
    # Hacer otro hilo que gestione la cola de los taxis

    # Bucle de gestión de taxis
    while True:
        #print("acabo de iterar")
        conexion, direccion = socketEscucha.accept()
        hiloTaxi = threading.Thread(target=gestionarTaxi, args=(conexion, direccion))
        hiloTaxi.start()

if __name__ == "__main__":
    main()
