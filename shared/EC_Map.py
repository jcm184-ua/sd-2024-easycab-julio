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
                if f"({i},{j})" in keys:
                    value = self.diccionarioPosiciones[f"({i},{j})"]
                    if value[0] == 'taxi':
                        print(f"{COLORES_ANSII.BACKGROUD_GREEN} {value[1]} {COLORES_ANSII.ENDC}", end="")
                    elif value[0] == 'cliente':
                        print(f"{COLORES_ANSII.BACKGROUD_YELLOW} {value[1]} {COLORES_ANSII.ENDC}", end="")
                    elif value[0] == 'localizacion':
                        print(f"{COLORES_ANSII.BACKGROUD_BLUE} {value[1]} {COLORES_ANSII.ENDC}", end="")
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

    map.diccionarioPosiciones.update({"(2,3)" : ('taxi',1)})
    map.diccionarioPosiciones.update({"(8,2)" : ('taxi', 2)})
    map.diccionarioPosiciones.update({"(3,5)" : ('cliente','d')})
    map.diccionarioPosiciones.update({"(9,15)" : ('localizacion','A')})
    map.diccionarioPosiciones.update({"(14,7)" : ('localizacion','C')})
    map.print()

    pruebaJson = map.exportJson()
    print(pruebaJson)

    map.clear()
    map.print()

    map.loadJson(pruebaJson)
    map.print()




if __name__ == "__main__":
    main()

