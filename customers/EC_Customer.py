import sys
import time
from kafka import KafkaProducer
from kafka import KafkaConsumer
import re

sys.path.append('../shared')
from EC_Map import Map
from EC_Shared import *

BROKER_IP = None
BROKER_PORT = None
BROKER_ADDR = None
ID = None

def comprobarArgumentos(argumentos):
    if len(argumentos) != 4:
        printInfo("ERROR LOS ARGUMENTOS. Necesito estos argumentos: <BROKER_IP> <BROKER_PORT> <ID>")
        exit()
    printInfo("Número de argumentos correcto.")

def asignarConstantes(argumentos):
    global BROKER_IP
    BROKER_IP = argumentos[1]
    global BROKER_PORT
    BROKER_PORT = int(argumentos[2])
    global BROKER_ADDR
    BROKER_ADDR = BROKER_IP+":"+str(BROKER_PORT)
    global ID
    ID = argumentos[3]
    printInfo("Constantes asignadas")

def leerServicios():
    # TODO: Leer fichero
    servicios = []
    servicios.append("E")
    servicios.append("A")
    servicios.append("D")
    return servicios

def esperarMensaje():
    conexion = conectarBrokerConsumidor(BROKER_ADDR, TOPIC_CLIENTES)
    for mensaje in conexion:
        print(f"DEBUG: Mensaje recibido: {mensaje.value.decode(FORMAT)}")
        camposMensaje = re.findall('[^\[\]]+', mensaje.value.decode(FORMAT))
        if camposMensaje[0] == f"EC_Central->EC_Customer_{ID}":
            conexion.close()
            printInfo("Desconectado del broker como consumidor.")
            return camposMensaje[1]

def evaluarMensaje(mensajeRecibido):
    if mensajeRecibido == "OK":
        return True
    elif mensajeRecibido == "KO":
        return False
    else:
        pass
        #TODO: Gestionar error

def solicitarServicio(servicio):
    printInfo(f"Procedo a solicitar el servicio {servicio}")
    publicarMensajeEnTopic(f"[EC_Customer_{ID}->EC_Central][{servicio}]", TOPIC_CLIENTES, BROKER_ADDR) # (Solicitar servicio

    mensajeRecibido = esperarMensaje()

    if evaluarMensaje(mensajeRecibido):
        printInfo("Me han aceptado y completado el servicio.")
    else:
        printInfo("Me han denegado o cancelado el servicio.")

def main():
    comprobarArgumentos(sys.argv)
    asignarConstantes(sys.argv)
    printInfo(f"BROKER_IP={BROKER_IP}, BROKER_PORT = {BROKER_PORT}, ID={ID}.")

    servicios = leerServicios()

    #conexionProductor = conectarBrokerProductor(BROKER_IP, BROKER_PORT)
    #conexionConsumidor = conectarBrokerConsumidor(BROKER_IP, BROKER_PORT)

    # TODO: ¿Comprobar la conexión, brocker puede caer?
    for servicio in servicios:
        solicitarServicio(servicio)
        printInfo("Esperando 4 segundos...")
        time.sleep(4)
    printInfo("He realizado todos los servicios que deseaba. Finalizando ejecución...")

if __name__ == "__main__":
    main()
