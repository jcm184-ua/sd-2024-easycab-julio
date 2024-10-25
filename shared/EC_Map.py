import tkinter as tk
import json
import threading
import re
from EC_Shared import *
from kafka import KafkaProducer, KafkaConsumer  # Importar KafkaProducer y KafkaConsumer

SIZE = 20
TILE_SIZE = 30  # Tamaño de cada celda del mapa

class COLORES_ANSII:
    #BLUE = '\033[94m'
    BACKGROUD_BLUE = '\033[104m'
    #YELLOW = '\033[93m'
    BACKGROUD_YELLOW = '\033[103m'
    #GREEN = '\033[92m'
    BACKGROUD_GREEN = '\033[102m'
    ENDC = '\033[0m'
    BACKGROUD_RED = '\033[101m'

class Map:
    diccionarioPosiciones = {}
    taxisActivos = []

    def print(self):
        """ Imprimir el mapa en consola """
        print("MAPA:")
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

    def draw_on_canvas(self, canvas):
        """ Dibujar el mapa en un Canvas de Tkinter """
        canvas.delete("all")  # Limpiar el canvas
        for i in range(SIZE):
            for j in range(SIZE):
                x1 = j * TILE_SIZE
                y1 = i * TILE_SIZE
                x2 = x1 + TILE_SIZE
                y2 = y1 + TILE_SIZE
                canvas.create_rectangle(x1, y1, x2, y2, outline="black")

                # Comprobar si hay algún elemento en la posición actual
                for key, value in self.diccionarioPosiciones.items():
                    if value == f"{i+1},{j+1}":
                        if key.startswith('taxi'):
                            canvas.create_rectangle(x1, y1, x2, y2, fill="green")
                            canvas.create_text((x1 + x2) // 2, (y1 + y2) // 2, text=key[5:], fill="white")
                        elif key.startswith('cliente'):
                            canvas.create_rectangle(x1, y1, x2, y2, fill="yellow")
                            canvas.create_text((x1 + x2) // 2, (y1 + y2) // 2, text=key[8:], fill="black")
                        elif key.startswith('localizacion'):
                            canvas.create_rectangle(x1, y1, x2, y2, fill="blue")
                            canvas.create_text((x1 + x2) // 2, (y1 + y2) // 2, text=key[13:], fill="white")
                        break

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
        initX = x
        initY = y
        #TODO: Comprobar límites del mapa y "overflowear" si se sale
        self.diccionarioPosiciones[key] = f"{int(initX)},{int(initY)}"
        print(f"INFO: Movimiento realizado a {initX},{initY} para {key}")

    def getPosition(self, key):
        try:
            self.diccionarioPosiciones[key]
            return self.diccionarioPosiciones[key]
        except:
            print("ERROR: No se ha encontrado la posición.")
            return None

# Función en segundo plano para leer de Kafka
def kafka_consumer_thread(topic, broker_addr, add_error_callback):
    consumer = conectarBrokerConsumidor(topic, broker_addr)
    for mensaje in consumer:
        camposMensaje = re.findall('[^\[\]]+', mensaje.value.decode(FORMAT))
        recibidor = camposMensaje[0].split("->")[0]
        add_error_callback(f"{recibidor}: {camposMensaje[1]}")

# Crear una ventana con un canvas para mostrar el mapa gráficamente
def create_window(map_instance):
    root = tk.Tk()
    root.title("Mapa de Taxis")

    # Frame para contener el mapa y el área de errores
    main_frame = tk.Frame(root)
    main_frame.pack(side=tk.LEFT)

    # Canvas para el mapa
    canvas = tk.Canvas(main_frame, width=SIZE * TILE_SIZE, height=SIZE * TILE_SIZE)
    canvas.pack(side=tk.LEFT)

    # Frame para los errores
    error_frame = tk.Frame(main_frame)
    error_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

    # Scrollbar y Text para los errores
    scrollbar = tk.Scrollbar(error_frame)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    error_text = tk.Text(error_frame, wrap=tk.WORD, yscrollcommand=scrollbar.set, height=20, width=40)
    error_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    scrollbar.config(command=error_text.yview)

    # Método para añadir errores al Text
    def addError(mensaje):
        error_text.insert(tk.END, mensaje + "\n")
        error_text.see(tk.END)  # Scrollea automáticamente al final

    # Dibuja el mapa en el canvas
    map_instance.draw_on_canvas(canvas)

    # Iniciar el hilo para consumir mensajes de Kafka
    topic = 'errores'
    broker_addr = 'localhost:20000'  # Reemplazar con tu dirección del broker
    threading.Thread(target=kafka_consumer_thread, args=(topic, broker_addr, addError), daemon=True).start()

    # Iniciar el hilo para producir mensajes de error de prueba
    threading.Thread(target=kafka_producer_thread, args=(topic, broker_addr), daemon=True).start()

    # Ejecutar el loop de Tkinter para mantener la ventana abierta
    root.mainloop()


# Ejemplo de uso
def main():
    map_instance = Map()

    # Imprimir el mapa inicial por consola
    map_instance.print()

    # Actualizar el mapa con taxis, clientes y localizaciones
    map_instance.diccionarioPosiciones.update({"taxi_1": "2,3"})
    map_instance.diccionarioPosiciones.update({"taxi_2": "8,2"})
    map_instance.diccionarioPosiciones.update({"cliente_d": "3,5"})
    map_instance.diccionarioPosiciones.update({"cliente_e": "7,8"})
    map_instance.diccionarioPosiciones.update({"localizacion_A": "9,15"})
    map_instance.diccionarioPosiciones.update({"localizacion_C": "14,7"})

    # Imprimir el mapa actualizado por consola
    map_instance.print()

    #mapa.diccionarioPosiciones.update({"localizacion_C" : "10,2"})
    #mapa.print()

    # Exportar el mapa a JSON
    pruebaJson = map_instance.exportJson()
    pruebaJson2 = map_instance.exportActiveTaxis()
    print("Exportado JSON:", pruebaJson, pruebaJson2)

    # Borrar el mapa en la consola
    map_instance.clear()
    map_instance.print()

    # Cargar el mapa desde JSON y mostrarlo por consola
    map_instance.loadJson(pruebaJson)
    map_instance.loadActiveTaxis(pruebaJson2)
    map_instance.print()

    # Mostrar el mapa gráficamente con Tkinter y consumir/ producir mensajes de Kafka
    create_window(map_instance)

if __name__ == "__main__":
    main()
