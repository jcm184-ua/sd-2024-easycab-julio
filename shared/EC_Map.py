import tkinter as tk
from tkinter import ttk
import json
import threading
import re
from EC_Shared import *
import time

from EC_Shared import *

SIZE = 20
TILE_SIZE = 30  # Tamaño de cada celda del mapa

class Map:
    diccionarioPosiciones = {}
    taxisActivos = []

    def print(self):
        """ Imprimir el mapa en consola """
        #print("MAPA:")
        #for key, value in self.diccionarioPosiciones.items():
        #    printDebug(f"{key} : {value}")
        for i in range(1, SIZE + 1):
            print("-" * int(((0.5 + SIZE) * 4 - 1)))
            print("|", end="")
            for j in range(1, SIZE + 1):
                taxi = " "
                localizacion = " "
                cliente = " "
                #time.sleep(0.1)
                elementos = []  # Lista para almacenar elementos en la misma posición
                for key, value in self.diccionarioPosiciones.items():
                #    print(f"{i},{j}")
                #    print(f"{key} : {value}", end="")
                 #   print(value == f"{i},{j}")
                    if value == f"{i},{j}":
                 #       print(f"{key} : {value}", end="")
                        if key.startswith('taxi'):
                            if key in self.taxisActivos:
                                taxi = f"{COLORES_ANSI.BACKGROUD_GREEN}{COLORES_ANSI.BLACK}{key[5:]}{COLORES_ANSI.BLACK}{COLORES_ANSI.END_C}"
                            else:
                                taxi = f"{COLORES_ANSI.BACKGROUD_RED}{COLORES_ANSI.BLACK}{key[5:]}{COLORES_ANSI.BLACK}{COLORES_ANSI.END_C}"
                        if key.startswith('localizacion'):
                            localizacion = f"{COLORES_ANSI.BACKGROUD_BLUE}{COLORES_ANSI.BLACK}{key[13:]}{COLORES_ANSI.BLACK}{COLORES_ANSI.END_C}"
                        if key.startswith('cliente'):
                            cliente = f"{COLORES_ANSI.BACKGROUD_YELLOW}{COLORES_ANSI.BLACK}{key[8:]}{COLORES_ANSI.BLACK}{COLORES_ANSI.END_C}"
                else:
                    print(taxi + localizacion + cliente, end="")
                print("|", end="")
            print()
        print("-" * int(((0.5+SIZE) * 4 - 1)))

    def draw_on_canvas(self, canvas):
        if canvas is not None:
            """ Dibujar el mapa en un Canvas de Tkinter """
            canvas.delete("all")  # Limpiar el canvas
            for i in range(SIZE):
                for j in range(SIZE):
                    x1 = j * TILE_SIZE
                    y1 = i * TILE_SIZE
                    x2 = x1 + TILE_SIZE
                    y2 = y1 + TILE_SIZE

                    elementos = []  # Lista para almacenar elementos en la misma posición
                    taxi_dibujado = False  # Indica si se ha dibujado un taxi
                    backgroud_color = "white"
                    # Verificar si hay localizaciones, taxis o clientes en la celda
                    for key, value in self.diccionarioPosiciones.items():
                        if value == f"{i+1},{j+1}":
                            if key.startswith('localizacion'):
                                backgroud_color = "dodgerBlue"
                                elementos.append(key[13:])  # Añadir nombre de la localización
                            elif key.startswith('taxi'):
                                taxi_dibujado = True  # Hay un taxi
                                if key in self.taxisActivos:
                                    backgroud_color = "limeGreen"
                                else:
                                    backgroud_color = "red"
                                elementos.append(key[5:])  # Añadir nombre del taxi
                            elif key.startswith('cliente'):
                                if not taxi_dibujado:  # Si no se ha dibujado un taxi
                                    backgroud_color = "yellow"
                                elementos.append(key[8:])  # Añadir nombre del cliente

                    # Si hay un cliente pero no un taxi, se dibuja en amarillo
                    if not taxi_dibujado and any(k.startswith('cliente') for k in self.diccionarioPosiciones.keys() if self.diccionarioPosiciones[k] == f"{i+1},{j+1}"):
                        canvas.create_rectangle(x1, y1, x2, y2, fill="yellow")  # Dibuja cliente en amarillo

                    canvas.create_rectangle(x1, y1, x2, y2, outline="black", fill=backgroud_color)


                    # Dibujar texto en la celda si hay elementos
                    if len(elementos) > 0:
                        # Elegir el color del texto basado en el tipo de elemento
                        text_color = "black"
                        canvas.create_text((x1 + x2) // 2, (y1 + y2) // 2, text=", ".join(elementos), fill=text_color)

            # Llamar a sí mismo después de 1000 ms (1 segundo)
            canvas.after(1000, lambda: self.draw_on_canvas(canvas))

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
def consumidorErrores(TOPIC_ERRORES_MAPA, BROKER_ADDR, add_error_callback):
    consumer = conectarBrokerConsumidor(BROKER_ADDR, TOPIC_ERRORES_MAPA)
    while True:
        for mensaje in consumer:
            camposMensaje = re.findall('[^\[\]]+', mensaje.value.decode(FORMAT))
            recibidor = camposMensaje[0].split("->")[0]
            add_error_callback(f"{recibidor}: {camposMensaje[1]}")

def consumidorEstados(TOPIC_ESTADOS_MAPA, BROKER_ADDR, add_taxi_callback, add_client_callback, clear_taxi_table_callback, clear_client_table_callback):
    consumer = conectarBrokerConsumidor(BROKER_ADDR, TOPIC_ESTADOS_MAPA)

    while True:
        for mensaje in consumer:
            try:
                taxis_clientes = {}
                data = json.loads(mensaje.value.decode('utf-8'))
                # Limpiar las tablas de taxis y clientes
                clear_taxi_table_callback()
                clear_client_table_callback()

                taxiID = None
                # Cargar los datos de los taxis
                for taxi in data.get("taxis", []):
                    taxiID = taxi.get("id")
                    taxiDestino = None
                    taxiEstado = None
                    clienteID = None
                    locID = None
                    if taxi.get("cliente"):
                        clienteID = taxi.get("cliente")
                        if taxi.get("destino"):
                            locID = taxi.get("destino")

                    if taxi.get("estado") == "OK":
                        if taxi.get("estado") == "servicio":
                            taxiEstado = f"OK. Servicio " + clienteID
                            taxiDestino = taxi.get("destino")
                        elif taxi.get("estado") == "enCamino":
                            taxiEstado = f"OK. Servicio " + clienteID
                            taxiDestino = clienteID
                        elif taxi.get("estado") == "esperando":
                            taxiEstado = f"OK. Parado"
                        elif taxi.get("estado") == "desconectado":
                            taxiEstado = f"KO. Parado"
                        else:
                            taxiEstado = taxi.get("estado")
                            taxiDestino = taxi.get("destino")
                    else:
                        if taxi.get("estado") == "servicio":
                            taxiDestino = taxi.get("destino")
                        elif taxi.get("estado") == "enCamino":
                            taxiDestino = clienteID

                        taxiEstado = f"KO. Parado"


                    add_taxi_callback(
                        taxiID,
                        taxiDestino,
                        taxiEstado
                    )

                    if clienteID:
                        taxis_clientes[clienteID] = [taxiID, locID, taxi["estado"]]

                # Cargar los datos de los clientes
                for cliente in data.get("clientes", []):
                    estadoTaxi = None
                    taxiID = None
                    locID = None


                    clienteID = cliente.get("id")

                    if clienteID in taxis_clientes.keys():
                        taxiID = taxis_clientes[clienteID][0]
                        locID = taxis_clientes[clienteID][1]
                        estadoTaxi = taxis_clientes[clienteID][2]

                    if estadoTaxi == "servicio":
                        clienteEstado = f"OK. En camino"
                    elif estadoTaxi == "enCamino":
                        clienteEstado = f"OK. Taxi " + taxiID
                    else:
                        clienteEstado = f"OK. Esperando."

                    add_client_callback(
                        clienteID,
                        locID,
                        clienteEstado
                    )
            except Exception as e:
                printError(f"Error al procesar mensaje: {e}")



def create_window(map_instance, BROKER_ADDR):
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
    taxi_table.column("ID", width=75)
    taxi_table.column("Destino", width=75)
    taxi_table.column("Estado", width=250)
    client_table.column("ID", width=75)
    client_table.column("Destino", width=75)
    client_table.column("Estado", width=250)

    # Método para añadir errores al Text
    def addError(mensaje):
        error_text.insert(tk.END, mensaje + "\n")
        error_text.see(tk.END)  # Scrollea automáticamente al final

    # Método para añadir un taxi a la tabla
    def add_taxi(id, destino, estado):
        if destino is None:
            destino = "-"
        taxi_table.insert("", tk.END, values=(id, destino, estado))

    # Método para añadir un cliente a la tabla
    def add_client(id, destino, estado):
        if destino is None:
            destino = "-"
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
    # Iniciar el hilo para consumir mensajes de Kafka
    #topic = 'errores'
    threading.Thread(target=consumidorErrores, args=(TOPIC_ERRORES_MAPA, BROKER_ADDR, addError), daemon=True).start()
    threading.Thread(target=consumidorEstados, args=(TOPIC_ESTADOS_MAPA, BROKER_ADDR, add_taxi, add_client, clear_taxi_table, clear_client_table), daemon=True).start()
    # Ejecutar el loop de Tkinter para mantener la ventana abierta
    root.mainloop()

def iniciarMapa(map_instance, BROKER_ADDR):
    # Mostrar el mapa gráficamente con Tkinter y consumir/ producir mensajes de Kafka
    create_window(map_instance, BROKER_ADDR)

"""
#Descomentar para pruebas
def main():
    map_instance = Map()
        # Imprimir el mapa inicial por consola
    map_instance.print()

    # Actualizar el mapa con taxis, clientes y localizaciones
    map_instance.diccionarioPosiciones.update({"taxi_1": "1,2"})
    map_instance.diccionarioPosiciones.update({"taxi_2": "8,2"})
    map_instance.diccionarioPosiciones.update({"taxi_3": "17,8"})
    map_instance.diccionarioPosiciones.update({"cliente_d": "8,9"})
    map_instance.diccionarioPosiciones.update({"cliente_e": "17,8"})
    map_instance.diccionarioPosiciones.update({"localizacion_A": "3,5"})
    map_instance.diccionarioPosiciones.update({"localizacion_B": "10,18"})
    map_instance.diccionarioPosiciones.update({"localizacion_C": "14,6"})

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

if __name__ == "__main__":
    main()
"""