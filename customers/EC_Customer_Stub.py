# hay que preguntar como serán los ficheros que lee EC_Customer, pero de momento se
# puedehacer el main, comprobarArgumentos, conexion al brocker y escritura en ella

import sys
import time
from kafka import KafkaProducer
from kafka import KafkaConsumer
import re

FORMAT = 'utf-8'

BROKER_IP = None
BROKER_PORT = None
BROKER_ADDR = None
ID = None

def comprobarArgumentos(argumentos):
    if len(argumentos) != 4:
        print("CHECKS: ERROR LOS ARGUMENTOS. Necesito estos argumentos: <BROKER_IP> <BROKER_PORT> <ID>")
        exit()
    print("INFO: Número de argumentos correcto.")


def asignarConstantes(argumentos):
    global BROKER_IP
    BROKER_IP = argumentos[1]
    global BROKER_PORT
    BROKER_PORT = int(argumentos[2])
    global BROKER_ADDR
    BROKER_ADDR = BROKER_IP+":"+str(BROKER_PORT)
    global ID
    ID = argumentos[3]


def leerServicios():
    # TODO: Leer fichero
    servicios = []
    servicios.append("E")
    servicios.append("A")
    servicios.append("D")
    return servicios

def publicarMensaje(mensaje):
    global BROKER_ADDR
    print(f"INFO: Conectando al broker en la dirección ({BROKER_ADDR}) como productor.")
    conexion = KafkaProducer(bootstrap_servers=BROKER_ADDR)
    conexion.send('CLIENTES',(mensaje.encode(FORMAT)))
    print(f"INFO: Mensaje {mensaje} publicado.")
    # TODO: Fallo de publicación.
    conexion.close()
    print("INFO: Desconectado del broker como productor.")

def conectarBrokerConsumidor():
    global BROKER_ADDR
    print(f"INFO: Conectando al broker en la dirección ({BROKER_ADDR}) como consumidor.")
    # return KafkaConsumer('CLIENTES',bootstrap_servers=CONEXION,auto_offset_reset='earliest')
    return KafkaConsumer('CLIENTES',bootstrap_servers=BROKER_ADDR)

def esperarMensaje():
    conexion = conectarBrokerConsumidor()
    for mensaje in conexion:
        print(f"DEBUG: Mensaje recibido -> {mensaje.value.decode(FORMAT)}")
        camposMensaje = re.findall('[^\[\]]+', mensaje.value.decode(FORMAT))
        if camposMensaje[0] == f"EC_Central->EC_Customer-{ID}":
            conexion.close()
            print("INFO: Desconectado del broker como consumidor.")
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
    print(f"INFO: Procedo a solicitar el servicio {servicio}")
    publicarMensaje(f"[EC_Customer_{ID}->EC_Central][{servicio}]") # (Solicitar servicio
    
    """mensajeRecibido = esperarMensaje()

    if evaluarMensaje(mensajeRecibido):
        print("INFO: Me han aceptado el servicio.")
    else:
        print("INFO: Me han denegado el servicio.")"""    

def main():
    comprobarArgumentos(sys.argv)
    asignarConstantes(sys.argv)
    print(f"INFO: BROKER_IP={BROKER_IP}, BROKER_PORT = {BROKER_PORT}, ID={ID}.")

    servicios = leerServicios()

    #conexionProductor = conectarBrokerProductor(BROKER_IP, BROKER_PORT)
    #conexionConsumidor = conectarBrokerConsumidor(BROKER_IP, BROKER_PORT)

    # TODO: ¿Comprobar la conexión, brocker puede caer?
    while True:
        for servicio in servicios:
            solicitarServicio(servicio)
            print("INFO: Esperando 4 segundos...")
            time.sleep(4)
    print("INFO: He realizado todos los servicios que deseaba. Finalizando ejecución...")

if __name__ == "__main__":
    main()
