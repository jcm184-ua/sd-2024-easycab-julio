import sys
import sqlite3
import socket
import threading

HEADER = 64
FORMAT = 'utf-8'

taxisConectados = 0
taxisLibres = 0

# mirar PROGRAMACION CONCURRENTE

def comprobarArgumentos(argumentos):
    #print(sys.argv)
    if len(argumentos) != 4:
        print("CHECKS: ERROR EN EL NÚMERO DE ARGUMENTOS")
        exit()
    print("INFO: Número de argumentos correcto.")

def leerMapa():
    if False:
        print("CHECKS: ERROR DE MAPA")
        exit
    print("INFO: Mapa cargado con éxito.")

def abrirSocket(host, puertoEscucha):
    #print("INFO: Abriendo socket de esucha en {0}, {1}.".format(host, puertoEscucha))
    print("INFO: Abriendo socket de esucha en el puerto {0}.".format(puertoEscucha))
    prueba = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    THIS_ADDR = (host, puertoEscucha)
    prueba.bind(THIS_ADDR)
    return prueba

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
    #Autenticar taxi
    if autenticarTaxi(conexion, direccion):
        modificarTaxisLibres(1)
        # Abrir un hilo que se encarge de leer los movimientos y actualizar el mapa a través del BROKER
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
    #if (autenticar_taxi):
    
    
    #else:
    #print("INFO: Taxi con conexion {0} y {1} no autorizado. Desconectando..."
    #    .format(conexion, direccion))
    #conexion.close()

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

    # TODO: por si ha crasheado, todos los taxis de la bbdd asignar desconectado.
    
    # DBIP = sys.argv[4]
    # DBPORT = sys.argv[5]

    leerMapa()

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

    while True:
        #print("acabo de iterar")
        conexion, direccion = socketEscucha.accept()
        modificarTaxisConectados(+1)
        hiloTaxi = threading.Thread(target=gestionarTaxi, args=(conexion, direccion))
        hiloTaxi.start()

if __name__ == "__main__":
    main()
