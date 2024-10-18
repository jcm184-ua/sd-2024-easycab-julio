# hay que preguntar como serán los ficheros que lee EC_Customer, pero de momento se
# puedehacer el main, comprobarArgumentos, conexion al brocker y escritura en ella

import sys
import socket
from kafka import KafkaProducer
from kafka import KafkaConsumer

FORMAT = 'utf-8'

def comprobarArgumentos(argumentos):
    if len(argumentos) != 4:
        print("CHECKS: ERROR LOS ARGUMENTOS. Necesito estos argumentos: <BROKER_IP> <BROKER_PORT> <ID>")
        exit()
    print("INFO: Número de argumentos correcto.")

def leerServicios(servicios):
    # Leer
    servicios.append("<20,10>")
    servicios.append("<7,12>")
    servicios.append("<15,4>")

def conectarBrokerProductor(BROKER_IP, BROKER_PORT):
    CONEXION = BROKER_IP+':'+BROKER_PORT
    print("INFO: Voy a conectarme al broker como productor.")
    return KafkaProducer(bootstrap_servers=CONEXION)

def conectarBrokerConsumidor(BROKER_IP, BROKER_PORT):
    CONEXION = BROKER_IP+':'+BROKER_PORT
    print("INFO: Voy a conectarme al broker como consumidor.")
    # return KafkaConsumer('CLIENTES',bootstrap_servers=CONEXION,auto_offset_reset='earliest')
    return KafkaConsumer('CLIENTES',bootstrap_servers=CONEXION)

def solicitarServicio(servicio, conexionProductor, conexionConsumidor):
    print("INFO: Procedo a solicitar el servicio {0}".format(servicio))
    conexionProductor.send('CLIENTES',servicio.encode(FORMAT))
    for message in conexionConsumidor:
        #print(message)
        #Si me aceptan
        if True:
            print("INFO: Me han aceptado el servicio.")
            realizarServicio(servicio, conectarBrokerConsumidor)
        else:
            print("INFO: Me han denegado el servicio.")

    
def realizarServicio(servicio, conexionConsumidor):
    #cuando me encuentre en casilla deseada o me notifiquen que ha terminado
    return True
    

def main():
    comprobarArgumentos(sys.argv)

    # Asignamos las constantes
    BROKER_IP = sys.argv[1]
    BROKER_PORT = sys.argv[2]
    ID = int(sys.argv[3])
    print("INFO: BROKER_IP={0}, BROKER_PORT = {1}, ID={2}.".format(BROKER_IP, BROKER_PORT, ID))

    servicios = []

    leerServicios(servicios)

    conexionProductor = conectarBrokerProductor(BROKER_IP, BROKER_PORT)
    conexionConsumidor = conectarBrokerConsumidor(BROKER_IP, BROKER_PORT)

    # ¿Comprobar la conexión, brocker puede caer?
    for servicio in servicios:
        solicitarServicio(servicio, conexionProductor, conexionConsumidor)
        print("INFO: Esperando 4 segundos...")
        sleep(4)
    print("INFO: He realizado todos los servicios que deseaba. Saliendo...")
    # CERRAR LAS CONEXIONES AL BROKER


if __name__ == "__main__":
    main()
