import os
import json

SIZE = 20

class COLORES_ANSII:
    BLUE = '\033[94m'
    BACKGROUD_BLUE = '\033[104m'
    YELLOW = '\033[93m'
    BACKGROUD_YELLOW = '\033[103m'
    GREEN = '\033[92m'
    BACKGROUD_GREEN = '\033[102m'
    ENDC = '\033[0m'

class Map:
    diccionarioPosiciones = {}

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
                            print(f"{COLORES_ANSII.BACKGROUD_GREEN} {key[5:]} {COLORES_ANSII.ENDC}", end="")
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

    def exportJson(self):
        return json.dumps(self.diccionarioPosiciones)

    def loadJson(self, jsonData):
        print(jsonData)
        self.diccionarioPosiciones = json.loads(jsonData)

# Ejemplo de uso
def main():
    map = Map()

    map.print()

    map.diccionarioPosiciones.update({"taxi_1" : "2,3"})
    map.diccionarioPosiciones.update({"taxi_2" : "8,2"})
    map.diccionarioPosiciones.update({"cliente_d" : "3,5"})
    map.diccionarioPosiciones.update({"cliente_e" : "7,8"})
    map.diccionarioPosiciones.update({"localizacion_A" : "9,15"})
    map.diccionarioPosiciones.update({"localizacion_C" : "14,7"})

    map.print()

    pruebaJson = map.exportJson()
    print(pruebaJson)

    map.clear()
    map.print()

    map.loadJson(pruebaJson)
    map.print()




if __name__ == "__main__":
    main()

