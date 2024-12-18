import socket, ssl

hostname = 'localhost'
port = 8443
cert = 'certServ.pem'

context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
context.load_cert_chain(cert, cert)
#context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
#context.load_cert_chain(certfile="mycertfile", keyfile="mykeyfile")

bindsocket = socket.socket()
bindsocket.bind((hostname, port))
bindsocket.listen(5)


def deal_with_client(connstream):
    data = connstream.recv(1024)
    # empty data means the client is finished with us    
    print('Recibido ', repr(data))
    #data = connstream.recv(1024)
    print("Enviando ADIOS")      
    connstream.send(b'ADIOS')
    


print('Escuchando en',hostname, port)

while True:
    newsocket, fromaddr = bindsocket.accept()
    connstream = context.wrap_socket(newsocket, server_side=True)
    print('Conexion recibida')
    try:
        deal_with_client(connstream)
    finally:
        connstream.shutdown(socket.SHUT_RDWR)
        connstream.close()

