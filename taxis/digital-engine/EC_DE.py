import sys

def comprobarArgumentos(argumentos):
    #print(sys.argv)
    if len(argumentos) != 8:
        print("CHECKS: ERROR EN EL NÚMERO DE ARGUMENTOS")
        exit()
    print("INFO: Número de argumentos correcto.")


def main():
    comprobarArgumentos(sys.argv)

    # Asignamos las constantes
    CENTRAL_IP = sys.argv[1]
    CENTRAL_PORT = sys.argv[2]
    BROKER_IP = sys.argv[3]
    BROKER_PORT = sys.argv[4]
    SENSOR_IP = sys.argv[5] # No debería el sensor conectarse al taxi? en tal caso innecesario
    SENSOR_PORT = sys.argv[6] # No debería el sensor conectarse al taxi? en tal caso innecesario
    ID = sys.argv[7]

    # Abrir un hilo con socket servidor para escuchar a un EC_S
    # esperar hasta que conecte un sensor para proseguir. Limitar a un máximo de un sensor

    # Abrir un hili socket cliente a main para autenticarse.
    # Aqui central verificará que su id existe en la base de datos y que está desconectado
    #                                               (garantizar que dos taxis no tienen mismo id)
    # socket / autenticarse()
    # una vez conectado el engine le dará la posición (por defecto x=1, y=1)

    # Permanecer a la espera de lo que se publica en el topic MOVIMIENTOS_TAXIS
    # Actualizar el mapa con topic MAPA

    # cuando reciba una solicitud de servicio moverse hacia alli con mover(origenx, origeny, destinoX, destinoY)
    # cuando tengas el mapa puedes diseñar la función moverse que vaya devolviendo los movimientos que te lleven a una posicion


if __name__ == "__main__":
    main()
