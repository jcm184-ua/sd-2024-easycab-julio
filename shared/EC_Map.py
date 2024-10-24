import os
import json

SIZE = 20

class COLORES_ANSII:
    #BLUE = '\033[94m'
    BACKGROUD_BLUE = '\033[104m'
    #YELLOW = '\033[93m'
    BACKGROUD_YELLOW = '\033[103m'
    #GREEN = '\033[92m'
    BACKGROUD_GREEN = '\033[102m'
    ENDC = '\033[0m'
    BACKGROUD_RED = '\033[101m'
    ENDC = '\033[0m'

class Map:
    diccionarioPosiciones = {}
    taxisActivos = []

    # TODO: Añadir aqui las localizaciones

    """def __init__(self):
        self.diccionarioPosiciones = {}"""

    """
    def imprimirCorrespondiente(valor, valor2):
        print(type(value))
        print(valor)
        if valor[0] == 'taxi':
            print(f"{COLORES_ANSII.BACKGROUD_GREEN}{valor[1]}{COLORES_ANSII.ENDC}")
        elif valor[0] == 'cliente':
            print(f"{COLORES_ANSII.BACKGROUD_YELLOW}{valor[1]}{COLORES_ANSII.ENDC}")
        elif valor[0] == 'localizacion':
            print(f"{COLORES_ANSII.BACKGROUD_BLUE}{valor[1]}{COLORES_ANSII.ENDC}")
    """

    def print(self):
        print("MAPA:")
        keys = self.diccionarioPosiciones.keys()
        for i in range(1, SIZE+1):
            print("-" * int(((0.5+SIZE) * 4 - 1)))
            print("|", end="")
            for j in range(1, SIZE+1):
                for key, value in self.diccionarioPosiciones.items():
                    if value == f"{i},{j}":
                        if key.startswith('taxi'):
                            if key in self.taxisActivos:
                                print(f"{COLORES_ANSII.BACKGROUD_GREEN} {key[5:]} {COLORES_ANSII.ENDC}", end="")
                            else:
                                print(f"{COLORES_ANSII.BACKGROUD_RED} {key[5:]} {COLORES_ANSII.ENDC}", end="")
                        elif key.startswith('cliente'):
                            print(f"{COLORES_ANSII.BACKGROUD_YELLOW} {key[8:]} {COLORES_ANSII.ENDC}", end="")
                        elif key.startswith('localizacion'):
                            print(f"{COLORES_ANSII.BACKGROUD_BLUE} {key[13:]} {COLORES_ANSII.ENDC}", end="")
                        break
                else:
                    print("   ", end="")
                print("|", end="")
            print()
        print("-" * int(((0.5+SIZE) * 4 - 1)))

    def clear(self):
        self.diccionarioPosiciones = {}
        self.taxisActivos = []

    def exportJson(self):
        return json.dumps(self.diccionarioPosiciones)

    def exportActiveTaxis(self):
        return json.dumps(self.taxisActivos)

    def loadJson(self, jsonData):
        self.diccionarioPosiciones = json.loads(jsonData)

    def loadActiveTaxis(self, jsonData):
        self.taxisActivos = json.loads(jsonData)

    def move(self, key, x, y):
        initX = self.diccionarioPosiciones[key].split(",")[0]
        initY = self.diccionarioPosiciones[key].split(",")[1]
        destX = int(initX) + x
        desrY = int(initY) + y
        #TODO: Comprobar límites del mapa y "overflowear" si se sale
        self.diccionarioPosiciones[key] = f"{int(int(initX) + x)},{int(int(initY) + y)}"
        print(f"INFO: Movimiento realizado de {initX},{initY} a {destX},{desrY} para {key}")

    def getPosition(self, key):
        try:
            self.diccionarioPosiciones[key]
            return self.diccionarioPosiciones[key]
        except:
            print("ERROR: No se ha encontrado la posición.")
            return None

# Ejemplo de uso
def main():
    mapa = Map()

    mapa.print()

    mapa.diccionarioPosiciones.update({"taxi_1" : "2,3"})
    mapa.taxisActivos = ["taxi_1"]
    mapa.diccionarioPosiciones.update({"taxi_2" : "8,2"})
    mapa.diccionarioPosiciones.update({"cliente_d" : "3,5"})
    mapa.diccionarioPosiciones.update({"cliente_e" : "7,8"})
    mapa.diccionarioPosiciones.update({"localizacion_A" : "9,15"})
    mapa.diccionarioPosiciones.update({"localizacion_C" : "14,7"})

    mapa.print()

    mapa.diccionarioPosiciones.update({"localizacion_C" : "10,2"})
    mapa.print()

    pruebaJson = mapa.exportJson()
    pruebaJson2 = mapa.exportActiveTaxis()
    print(pruebaJson)

    mapa.clear()
    mapa.print()

    mapa.loadJson(pruebaJson)
    mapa.loadActiveTaxis(pruebaJson2)
    mapa.print()




if __name__ == "__main__":
    main()

