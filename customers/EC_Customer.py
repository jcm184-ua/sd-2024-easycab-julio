import sys
import time
from kafka import KafkaProducer
from kafka import KafkaConsumer
import re
import json
import threading

sys.path.append('../shared')
from EC_Map import Map
from EC_Shared import *

BROKER_IP = None
BROKER_PORT = None
BROKER_ADDR = None
ID = None

servicios = []

def comprobarArgumentos(argumentos):
    if len(argumentos) != 4:
        printError("Necesito estos argumentos: <BROKER_IP> <BROKER_PORT> <ID>")
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
    global servicios
    try:
        with open('./EC_Requests.json') as json_file:
            jsonServicios = json.load(json_file)
            for request in jsonServicios['Requests']:
                printInfo(f"Cargando servicio {request['Id']}.")
                servicios.append(request['Id'])

            #printDebug(servicios)
            printInfo("Servicios cargados con éxito.")
    except IOError as error:
        printInfo("FATAL: No se ha podido abrir el fichero.")
        sys.exit()


def esperarMensaje():
    global enServicio

    conexion = conectarBrokerConsumidor(BROKER_ADDR, TOPIC_CLIENTES)
    while True:
        for mensaje in conexion:
            #printDebug(f"Mensaje recibido: {mensaje.value.decode(FORMAT)}")
            camposMensaje = re.findall('[^\[\]]+', mensaje.value.decode(FORMAT))
            if camposMensaje[0] == f"EC_Central->EC_Customer_{ID}":
            
                if camposMensaje[1] == "OK":
                    enServicio = True
                    printInfo("Me han aceptado el servicio.")
                    
                elif camposMensaje[1] == "KO":
                    enServicio = False   
                    printInfo("Me han denegado el servicio.")
                    break
                
                elif camposMensaje[1] == "RECOGIDO":
                    enServicio = True
                    printInfo("Me han recogido.")
                
                elif camposMensaje[1] == "EN_DESTINO":
                    enServicio = False
                    printInfo("Me han dejado en destino.")
                    break
            
        if not enServicio:
            break
            #conexion.close()
            #printInfo("Desconectado del broker como consumidor.")
            #return camposMensaje[1]

def evaluarMensaje(mensajeRecibido):
    if mensajeRecibido == "OK":
        return True
    elif mensajeRecibido == "KO":
        return False
    else:
        pass
        #TODO: Gestionar error

def solicitarServicio(servicio):
    printInfo(f"Procedo a solicitar el servicio {servicio}.")
    publicarMensajeEnTopic(f"[EC_Customer_{ID}->EC_Central][{servicio}]", TOPIC_CLIENTES, BROKER_ADDR) # (Solicitar servicio

    esperarMensaje()
    #threading.Thread(target=esperarMensaje).start()

    #if evaluarMensaje(mensajeRecibido):
    #    printInfo("Me han aceptado y completado el servicio.")
    #else:
    #    printInfo("Me han denegado o cancelado el servicio.")

def main():
    global enServicio
    enServicio = False

    comprobarArgumentos(sys.argv)
    asignarConstantes(sys.argv)
    leerServicios()

    global servicios
    for servicio in servicios:
        while enServicio:
            printInfo("Esperando a que finalice el servicio anterior...")
            time.sleep(1)
        
        solicitarServicio(servicio)

        

        printInfo("Esperando 4 segundos...")
        time.sleep(4)
    printInfo("He realizado todos los servicios que deseaba. Finalizando ejecución...")

if __name__ == "__main__":
    main()
