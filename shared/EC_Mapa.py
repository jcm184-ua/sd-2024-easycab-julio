import os

SIZE = 20

class Map:
    diccionarioPosiciones = {}

    def display(self):
        print("MAPA:")
        keys = self.diccionarioPosiciones.keys()
        for i in range(1, SIZE+1):
            print("-" * int(((0.5+SIZE) * 4 - 1)))
            print("| ", end="")
            for j in range(1, SIZE+1):
                if (i, j) in keys:
                    print(self.diccionarioPosiciones[(i,j)], end="")
                else:
                    print(" ", end="")
                print(" | ", end="")
            print()
        print("-" * int(((0.5+SIZE) * 4 - 1)))

# Ejemplo de uso
def main():
    map = Map()

    map.display()

    map.diccionarioPosiciones.update({(2,3) : 'X'})

    map.display()

if __name__ == "__main__":
    main()

