import sys
import socket

HOST = 'localhost'

def comprobarArgumentos(argumentos):
    #print(sys.argv)
    if len(argumentos) != 6:
        print("CHECKS: ERROR EN EL NÚMERO DE ARGUMENTOS")
        exit()
    print("CHECKS: Número de argumentos correcto.")

def main():
    print("Hello World!")
    comprobarArgumentos(sys.argv)
    LISTENPORT = sys.argv[1]
    ipBroker = sys.argv[2]
    puertoBroker = sys.argv[3]
    ipBBDD = sys.argv[4]
    puertoBBDD = sys.argv[5]

    # escucha concurrente



if __name__ == "__main__":
    main()
