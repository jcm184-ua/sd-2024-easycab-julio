import os

# Definir constantes
SIZE = 20
EMPTY = ' '
TAXI_MOVING = 'T'  # Verde si está en movimiento
TAXI_STOPPED = 't'  # Rojo si está parado
LOCATION = 'L'  # Localizaciones de servicio
CLIENT = 'C'  # Clientes solicitando taxi

class Map:
    def __init__(self):
        # Inicializar el mapa con celdas vacías
        self.grid = [[EMPTY for _ in range(SIZE)] for _ in range(SIZE)]
    
    def display_map(self):
        os.system('cls' if os.name == 'nt' else 'clear')  # Limpiar la pantalla
        for row in self.grid:
            print(" | ".join(row))
            print("-" * (SIZE * 4 - 1))  # Divisor para cada fila
    
    def add_taxi(self, x, y, moving=True):
        """Añadir un taxi en la posición (x, y)"""
        self.grid[x][y] = TAXI_MOVING if moving else TAXI_STOPPED
    
    def add_location(self, x, y):
        """Añadir una localización en la posición (x, y)"""
        self.grid[x][y] = LOCATION
    
    def add_client(self, x, y):
        """Añadir un cliente en la posición (x, y)"""
        self.grid[x][y] = CLIENT

    def move_taxi(self, x_old, y_old, x_new, y_new, moving=True):
        """Mover el taxi de la posición (x_old, y_old) a (x_new, y_new)"""
        self.grid[x_old][y_old] = EMPTY
        self.add_taxi(x_new, y_new, moving)

    def clear_position(self, x, y):
        """Vaciar una celda del mapa"""
        self.grid[x][y] = EMPTY

    def wrap_position(self, x, y):
        """Geometría esférica: conectar bordes del mapa"""
        return x % SIZE, y % SIZE

# Ejemplo de uso
def main():
    city_map = Map()
    
    # Añadir taxis, localizaciones y clientes aleatorios
    city_map.add_taxi(1, 1, moving=True)
    city_map.add_location(5, 10)
    city_map.add_client(3, 7)

    # Mostrar el mapa inicial
    city_map.display_map()

    # Mover taxi
    old_x, old_y = 1, 1
    new_x, new_y = city_map.wrap_position(2, 2)
    city_map.move_taxi(old_x, old_y, new_x, new_y, moving=False)

    # Mostrar el mapa después de mover el taxi
    city_map.display_map()

if __name__ == "__main__":
    main()

