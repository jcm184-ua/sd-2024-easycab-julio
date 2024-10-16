import sys
import json
import sqlite3
import socket
import threading
from kafka import KafkaConsumer 

HEADER = 64
FORMAT = 'utf-8'

taxisConectados = 0
taxisLibres = 0

def comprobarArgumentos(argumentos):
    if len(argumentos) != 4:
        print("CHECKS: ERROR LOS ARGUMENTOS. Necesito estos argumentos: <LISTEN_PORT> <BROKER_IP> <BROKER_PORT>")
        exit()
    print("INFO: Número de argumentos correcto.")

def leerConfiguracionMapa():
    try: 
        with open('./EC_locations.json') as json_file:
            data = json.load(json_file)
            print("INFO: Mapa cargado con éxito.")
            print (data)
            # return data
    except IOError as error:
        print("FATAL: No se ha podido abrir el fichero.")
        sys.exit()


def abrirSocket(host, puertoEscucha):
    print("INFO: Abriendo socket de escuha en el puerto {0}.".format(puertoEscucha))
    socketAbierto = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    THIS_ADDR = (host, puertoEscucha)
    socketAbierto.bind(THIS_ADDR)
    return socketAbierto

def gestionarClientes(brokerHost, puertoEscucha):
    print("INFO: Conectando al broker con IP {0} en el puerto {1}.".format(brokerHost, puertoEscucha))
    #try:
    consumidor = KafkaConsumer('CLIENTES',bootstrap_servers=brokerHost+':'+str(puertoEscucha)) # ,auto_offset_reset='earliest')
    for mensaje in consumidor:
        #print(mensaje)
        print(mensaje.value.decode(FORMAT))
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
        modificarTaxisLibres(1)
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

def iniciarServicio():
    print("INFO: Iniciando servicio del taxi n($id) al cliente n($id).")
    #Iteramos sobre los taxis que disponemos con la info de la bbdd, buscamos el más cercano y lo despachamos.

def servicioFinalizado():
    print("INFO: Servicio del taxi n($id) al cliente n($id) finalizado.")
    modificarTaxisLibres(+1)

def main():
    comprobarArgumentos(sys.argv)

    # Asignamos las constantes
    HOST = "" # Simbólico, nos permite escuchar en todas las interfaces de red
    LISTEN_PORT = int(sys.argv[1])
    BROKER_IP = sys.argv[2]
    BROKER_PORT = int(sys.argv[3])
    ADDR_BROKER = (BROKER_IP, BROKER_PORT)

    # TODO: por si ha crasheado, todos los taxis de la bbdd asignar desconectado, posicion 0, 0
    
    # DBIP = sys.argv[4]
    # DBPORT = sys.argv[5]

    leerConfiguracionMapa()

    socketEscucha = abrirSocket(HOST, LISTEN_PORT)
    socketEscucha.listen()
    
    print("INFO: Entrando al bucle de ejecución...")

    #modificarTaxisLibres(taxisLibres, 2)

    # Crear hilo que se encarga de leer peticiones de clientes y les asigna su taxi.
        # dentro: ocurre una llamada de un cliente
    # if taxisLibres > 0:
    #     modificarTaxisLibres(-1)
    #    iniciarServicio()
    # else:
        #denegar servicio
        #print("CENTRAL: Denegado servicio a cliente n($id) por falta de taxis.")

    hiloClientes = threading.Thread(target=gestionarClientes, args=(BROKER_IP, BROKER_PORT))
    hiloClientes.start()
    # Hacer un hilo que gestione la cola de los clientes
    # Hacer otro hilo que gestione la cola de los taxis 

    # Bucle de gestión de taxis
    while True:
        #print("acabo de iterar")
        conexion, direccion = socketEscucha.accept()
        modificarTaxisConectados(+1)
        hiloTaxi = threading.Thread(target=gestionarTaxi, args=(conexion, direccion))
        hiloTaxi.start()

if __name__ == "__main__":
    main()
