import tkinter as tk
from tkinter import ttk
import json
import threading
import re
from EC_Shared import *
import time
from kafka import KafkaProducer, KafkaConsumer  # Importar KafkaProducer y KafkaConsumer

SIZE = 20
TILE_SIZE = 30  # Tamaño de cada celda del mapa

class COLORES_ANSII:
    BLACK = '\033[30m'
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
        #print("MAPA:")
        for i in range(1, SIZE + 1):
            print("-" * int(((0.5 + SIZE) * 4 - 1)))
            print("|", end="")
            for j in range(1, SIZE + 1):
                elementos = []  # Lista para almacenar elementos en la misma posición
                for key, value in self.diccionarioPosiciones.items():
                    if value == f"{i},{j}":
                        if key.startswith('taxi'):
                            if key in self.taxisActivos:
                                print(f"{COLORES_ANSII.BACKGROUD_GREEN}{COLORES_ANSII.BLACK}{key[5:]}{COLORES_ANSII.BLACK}{COLORES_ANSII.ENDC}", end="")
                            else:
                                print(f"{COLORES_ANSII.BACKGROUD_RED}{COLORES_ANSII.BLACK}{key[5:]}{COLORES_ANSII.BLACK}{COLORES_ANSII.ENDC}", end="")
                        else:
                            print(f" ", end="")
                        if key.startswith('localizacion'):
                            print(f"{COLORES_ANSII.BACKGROUD_BLUE}{COLORES_ANSII.BLACK}{key[13:]}{COLORES_ANSII.BLACK}{COLORES_ANSII.ENDC}", end="")
                        else:
                            print(f" ", end="")
                        if key.startswith('cliente'):
                            print(f"{COLORES_ANSII.BACKGROUD_YELLOW}{COLORES_ANSII.BLACK}{key[8:]}{COLORES_ANSII.BLACK}{COLORES_ANSII.ENDC}", end="")
                        else:
                            print(f" ", end="")
                        break
                else:
                    print("   ", end="")
                print("|", end="")
            print()
        print("-" * int(((0.5+SIZE) * 4 - 1)))

    def draw_on_canvas(self, canvas):
        print("Dibujando mapa...")
        if canvas is not None:

            """ Dibujar el mapa en un Canvas de Tkinter """
            canvas.delete("all")  # Limpiar el canvas
            for i in range(SIZE):
                for j in range(SIZE):
                    x1 = j * TILE_SIZE
                    y1 = i * TILE_SIZE
                    x2 = x1 + TILE_SIZE
                    y2 = y1 + TILE_SIZE

                    # Dibuja el rectángulo para la celda
                    canvas.create_rectangle(x1, y1, x2, y2, outline="black")

                    elementos = []  # Lista para almacenar elementos en la misma posición
                    for key, value in self.diccionarioPosiciones.items():
                        if value == f"{i+1},{j+1}":
                            if key.startswith('localizacion'):
                                canvas.create_rectangle(x1, y1, x2, y2, fill="dodgerBlue")
                                elementos.append(key[13:])  # Añadir nombre de la localización
                            elif key.startswith('cliente'):
                                canvas.create_rectangle(x1, y1, x2, y2, fill="yellow")
                                elementos.append(key[8:])  # Añadir nombre del cliente
                            elif key.startswith('taxi'):
                                if key in self.taxisActivos:
                                    canvas.create_rectangle(x1, y1, x2, y2, fill="limeGreen")  # Color para taxi activo
                                else:
                                    canvas.create_rectangle(x1, y1, x2, y2, fill="red")  # Color para taxi no activo
                                elementos.append(key[5:])  # Añadir nombre del taxi

                    # Dibujar texto en la celda si hay elementos
                    if len(elementos) > 0:
                        # Elegir el color del texto basado en el tipo de elemento
                        text_color = "black"
                        canvas.create_text((x1 + x2) // 2, (y1 + y2) // 2, text=", ".join(elementos), fill=text_color)
            # Llamar a sí mismo después de 1000 ms (1 segundo)
            #self.after(1000, lambda: self.draw_on_canvas(canvas))

    def clear(self):
        self.diccionarioPosiciones = {}
        self.taxisActivos = []

    def exportJson(self):
        return json.dumps(self.diccionarioPosiciones)

    def exportActiveTaxis(self):
        return (json.dumps(self.taxisActivos).replace("[", "(").replace("]", ")"))

    def loadJson(self, jsonData):
        self.diccionarioPosiciones = json.loads(jsonData)

    def loadActiveTaxis(self, jsonData):
        self.taxisActivos = json.loads(jsonData.replace("(", "[").replace(")", "]"))

    def setPosition(self, key, x, y):
        self.diccionarioPosiciones[key] = f"{x},{y}"
        #printDebug(f"Posición de {key} establecida en {x},{y}")

    def move(self, key, x, y):
        initX = x
        initY = y
        self.diccionarioPosiciones[key] = f"{int(initX)},{int(initY)}"
        printInfo(f"Movimiento realizado a {initX},{initY} para {key}")

    def getPosition(self, key):
        if key not in self.diccionarioPosiciones:
            #printDebug(f"No se ha encontrado {key} en el mapa.")
            return None
        else:
            self.diccionarioPosiciones[key]
            return self.diccionarioPosiciones[key]

    def activateTaxi(self, idTaxi):
        self.taxisActivos.append(f"taxi_{idTaxi}")

    def deactivateTaxi(self, idTaxi):
        #No deberia protegerlo aqui pero anyway
        if f"taxi_{idTaxi}" in self.taxisActivos:
            self.taxisActivos.remove(f"taxi_{idTaxi}")
        else:
            printWarning(f"Has intentado eliminar el taxi {idTaxi} que no estaba activo.")

# Función en segundo plano para leer de Kafka
def consumidorErrores(topic, broker_addr, add_error_callback):
    consumer = conectarBrokerConsumidor(topic, broker_addr)
    for mensaje in consumer:
        camposMensaje = re.findall('[^\[\]]+', mensaje.value.decode(FORMAT))
        recibidor = camposMensaje[0].split("->")[0]
        add_error_callback(f"{recibidor}: {camposMensaje[1]}")

def create_window(map_instance):
    root = tk.Tk()
    root.title("Mapa de Taxis")

    # Frame principal
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

    # Frame para las tablas de taxis y clientes
    table_frame = tk.Frame(main_frame)
    table_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

    # Tabla de taxis
    taxi_label = tk.Label(table_frame, text="TAXIS", font=("Arial", 14))
    taxi_label.pack(side=tk.TOP)

    taxi_table_frame = tk.Frame(table_frame)  # Frame para la tabla de taxis y su scrollbar
    taxi_table_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

    taxi_table = ttk.Treeview(taxi_table_frame, columns=("ID", "Destino", "Estado"), show="headings")
    taxi_table.heading("ID", text="ID")
    taxi_table.heading("Destino", text="Destino")
    taxi_table.heading("Estado", text="Estado")
    taxi_table.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    taxi_scrollbar = tk.Scrollbar(taxi_table_frame, orient="vertical", command=taxi_table.yview)
    taxi_table.configure(yscrollcommand=taxi_scrollbar.set)
    taxi_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    # Tabla de clientes
    client_label = tk.Label(table_frame, text="CLIENTES", font=("Arial", 14))
    client_label.pack(side=tk.TOP)

    client_table_frame = tk.Frame(table_frame)  # Frame para la tabla de clientes y su scrollbar
    client_table_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

    client_table = ttk.Treeview(client_table_frame, columns=("ID", "Destino", "Estado"), show="headings")
    client_table.heading("ID", text="ID")
    client_table.heading("Destino", text="Destino")
    client_table.heading("Estado", text="Estado")
    client_table.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    client_scrollbar = tk.Scrollbar(client_table_frame, orient="vertical", command=client_table.yview)
    client_table.configure(yscrollcommand=client_scrollbar.set)
    client_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    # Configurar el tamaño de las columnas de las tablas
    taxi_table.column("ID", width=100)
    taxi_table.column("Destino", width=150)
    taxi_table.column("Estado", width=100)
    client_table.column("ID", width=100)
    client_table.column("Destino", width=150)
    client_table.column("Estado", width=100)

    # Método para añadir errores al Text
    def addError(mensaje):
        error_text.insert(tk.END, mensaje + "\n")
        error_text.see(tk.END)  # Scrollea automáticamente al final

    # Método para añadir un taxi a la tabla
    def add_taxi(id, destino, estado):
        taxi_table.insert("", tk.END, values=(id, destino, estado))

    # Método para añadir un cliente a la tabla
    def add_client(id, destino, estado):
        client_table.insert("", tk.END, values=(id, destino, estado))

    # Método para limpiar la tabla de taxis
    def clear_taxi_table():
        for row in taxi_table.get_children():
            taxi_table.delete(row)

    # Método para limpiar la tabla de clientes
    def clear_client_table():
        for row in client_table.get_children():
            client_table.delete(row)

    # Dibuja el mapa en el canvas
    threading.Thread(target=map_instance.draw_on_canvas, args=(canvas,), daemon=True).start()

    #load_data_from_json("jsonPrueba.json", add_taxi, add_client, clear_taxi_table, clear_client_table)
    # Iniciar el hilo para consumir mensajes de Kafka
    #topic = 'errores'
    #broker_addr = 'localhost:20000'  # Reemplazar con tu dirección del broker
    #threading.Thread(target=consumidorErrores, args=(topic, broker_addr, addError), daemon=True).start()

    # Ejecutar el loop de Tkinter para mantener la ventana abierta
    root.mainloop()

def load_data_from_json(filename, add_taxi, add_client, clear_taxi_table, clear_client_table):
    # Limpiar tabla de taxis
    clear_taxi_table()

    # Limpiar tabla de clientes
    clear_client_table()

    with open(filename, 'r') as file:
        data = json.load(file)

        # Cargar taxis
        for taxi in data["taxis"]:
            add_taxi(taxi["id"], taxi["destino"], taxi["estado"])

        # Cargar clientes
        for cliente in data["clientes"]:
            add_client(cliente["id"], cliente["destino"], cliente["estado"])

# Ejemplo de uso
def main():
    map_instance = Map()

    # Imprimir el mapa inicial por consola
    map_instance.print()

    # Actualizar el mapa con taxis, clientes y localizaciones
    map_instance.diccionarioPosiciones.update({"taxi_1": "1,2"})
    map_instance.diccionarioPosiciones.update({"taxi_2": "8,2"})
    map_instance.diccionarioPosiciones.update({"taxi_3": "17,8"})
    map_instance.diccionarioPosiciones.update({"cliente_d": "8,9"})
    map_instance.diccionarioPosiciones.update({"cliente_e": "7,8"})
    map_instance.diccionarioPosiciones.update({"localizacion_A": "3,5"})
    map_instance.diccionarioPosiciones.update({"localizacion_C": "10,4"})

    map_instance.taxisActivos.append("taxi_1")
    map_instance.taxisActivos.append("taxi_3")

    # Imprimir el mapa actualizado por consola
    map_instance.print()

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

    map_instance.iniciarMapa()



if __name__ == "__main__":
    main()