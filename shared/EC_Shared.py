from datetime import datetime
import socket
from kafka import KafkaConsumer, KafkaProducer
import json

HEADER = 64
FORMAT = 'utf-8'

TOPIC_TAXIS = 'TAXIS'
TOPIC_CLIENTES = 'CLIENTES'
TOPIC_ERRORES_MAPA = 'ERRORES_MAPA'
TOPIC_ESTADOS_MAPA = 'ESTADOS_MAPA'

def printInfo(mensaje):
    print(datetime.now(), f"INFO: {mensaje}")

def printWarning(mensaje):
    print(datetime.now(), f"WARNING: {mensaje}")

def printError(mensaje):
    print(datetime.now(), f"ERROR: {mensaje}")

def abrirSocketServidor(socket_addr):
    printInfo(f"Abriendo socket servidor en la dirección {socket_addr}.")
    socketAbierto = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Evitar "OSError: [Errno 98] Address already in use" al matar y relanzar el servidor.
    socketAbierto.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    socketAbierto.bind(socket_addr)
    return socketAbierto

def abrirSocketCliente(socket_addr):
    printInfo(f"Abriendo socket cliente en la dirección {socket_addr}.")
    socketAbierto = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    socketAbierto.connect(socket_addr)
    return socketAbierto

def enviarMensajeServidor(conexion, mensaje):
    mensaje_codificado = mensaje.encode(FORMAT)
    longitud_mensaje = len(mensaje_codificado)
    longitud_envio = str(longitud_mensaje).encode(FORMAT)
    longitud_envio += b' ' * (HEADER - len(longitud_envio))
    conexion.send(longitud_envio)
    conexion.send(mensaje_codificado)
    printInfo(f"Mensaje '{mensaje}' enviado a través de conexión {conexion.getpeername()}.")

def recibirMensajeServidor(conexion):
    longitud_mensaje = conexion.recv(HEADER).decode(FORMAT)
    if longitud_mensaje:
        longitud_mensaje = int(longitud_mensaje)
        mensaje = conexion.recv(longitud_mensaje).decode(FORMAT)
        printInfo(f"Mensaje '{mensaje}' recibido a través de la conexión {conexion.getpeername()}.")
        return mensaje

def recibirMensajeServidorSilent(conexion):
    longitud_mensaje = conexion.recv(HEADER).decode(FORMAT)
    if longitud_mensaje:
        longitud_mensaje = int(longitud_mensaje)
        mensaje = conexion.recv(longitud_mensaje).decode(FORMAT)
        return mensaje

def enviarMensajeCliente(socket, mensaje):
    mensaje_codificado = mensaje.encode(FORMAT)
    longitud_mensaje = len(mensaje_codificado)
    longitud_envio = str(longitud_mensaje).encode(FORMAT)
    longitud_envio += b' ' * (HEADER - len(longitud_envio))
    socket.send(longitud_envio)
    socket.send(mensaje_codificado)
    printInfo(f"Mensaje '{mensaje}' enviado a través de conexión {socket.getsockname()}.")

def recibirMensajeCliente(conexion):
    longitud_mensaje = conexion.recv(HEADER).decode(FORMAT)
    if longitud_mensaje:
        longitud_mensaje = int(longitud_mensaje)
        mensaje = conexion.recv(longitud_mensaje).decode(FORMAT)
        printInfo(f"Mensaje '{mensaje}' recibido a través de la conexión {conexion.getsockname()}.")
        return mensaje

def recibirMensajeClienteSilent(conexion):
    longitud_mensaje = conexion.recv(HEADER).decode(FORMAT)
    if longitud_mensaje:
        longitud_mensaje = int(longitud_mensaje)
        mensaje = conexion.recv(longitud_mensaje).decode(FORMAT)
        return mensaje

def conectarBrokerConsumidor(broker_addr, topic):
    printInfo(f"Conectando al broker en la dirección ({broker_addr}), topic {topic} como consumidor.")
    # return KafkaConsumer('CLIENTES',bootstrap_servers=CONEXION,auto_offset_reset='earliest')
    return KafkaConsumer(topic,bootstrap_servers=broker_addr)

def publicarMensajeEnTopic(mensaje, topic, broker_addr):
    printInfo(f"Conectando al broker en la dirección ({broker_addr}) como productor.")
    conexion = KafkaProducer(bootstrap_servers=broker_addr)
    conexion.send(topic,(mensaje.encode(FORMAT)))
    printInfo(f"Mensaje {mensaje} publicado en topic {topic}.")
    # TODO: Fallo de publicación.
    conexion.close()
    printInfo("Desconectado del broker como productor.")

def enviarJSONEnTopic(data, topic, broker_addr):
    try:
        printInfo(f"Conectando al broker en la dirección ({broker_addr}) como productor.")
        conexion = KafkaProducer(bootstrap_servers=broker_addr)

        # Enviar el mensaje al topic
        conexion.send(topic, data.encode(FORMAT))  # Asegúrate de que FORMAT es correcto
        conexion.flush()
        
        printInfo(f"Mensaje JSON enviado: {data} en topic {topic}.")
    
    except Exception as e:
        print(f"Error al enviar el mensaje JSON en el topic: {e}")
    
    finally:
        conexion.close()
        printInfo("Desconectado del broker como productor.")