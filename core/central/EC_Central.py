import sys
import sqlite3
import socket
import threading

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
    prueba.bind((host, puertoEscucha))
    return prueba

def modificarTaxisConectados(taxis, cambio):
    taxis = taxis + cambio
    print("INFO: Número de taxis conectados actualizado: {0}".format(taxis))

def modificarTaxisLibres(taxis, cambio):
    taxis = taxis + cambio
    print("INFO: Número de taxis libres actualizado: {0}".format(taxis))

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
    # DBIP = sys.argv[4]
    # DBPORT = sys.argv[5]

    leerMapa()

    socketEscucha = abrirSocket(HOST, LISTEN_PORT)
    socketEscucha.listen()
    
    taxisConectados = 0
    taxisLibres = 0
    print("INFO: Entrando al bucle de ejecución...")

    modificarTaxisLibres(taxisLibres, 2)

    while True:
        print("acabo de iterar")
        conexion, direccion = socketEscucha.accept()
        modificarTaxisConectados(taxisConectados, +1)


    modificarTaxisLibres(1)
    modificarTaxisLibres(-4)
    
    # ocurre una llamada de un cliente
    if taxisLibres > 0:
        modificarTaxisLibres(-1)
        iniciarServicio()
    else:
        #denegar servicio
        print("CENTRAL: Denegado servicio a cliente n($id) por falta de taxis.")

if __name__ == "__main__":
    main()
