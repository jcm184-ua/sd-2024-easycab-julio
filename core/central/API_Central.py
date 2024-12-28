import json
import sys

sys.path.append('../../shared')
from EC_Shared import *

app = Flask(__name__)
CORS(app)


def comprobarArgumentos(argumentos):
    if len(argumentos) != 2:
        exitFatal("Necesito estos argumentos: <HOST> <LISTEN_PORT>")
    printInfo("Número de argumentos correcto.")

def asignarConstantes(argumentos):
    global HOST
    HOST = argumentos[1]
    global LISTEN_PORT
    LISTEN_PORT = int(argumentos[2])
    printInfo("Constantes asignadas.")

def exportDB():
    conexion, cursor = generarConexionBBDD(DATABASE_USER, DATABASE_PASSWORD)

    try:
        # Consultar datos de la tabla de taxis
        cursor.execute("SELECT id, estado, sensores, posicion, cliente, destino FROM taxis")
        taxis = [
            {
                "id": row[0],
                "estado": row[1],
                "sensores": row[2],
                "posicion": row[3],
                "cliente": row[4],
                "destino": row[5],
                "token": row[6]
            }
            for row in cursor.fetchall()
        ]

        # Consultar datos de la tabla de clientes
        cursor.execute("SELECT id, posicion FROM clientes")
        clientes = [
            {
                "id": row[0],
                "posicion": row[1]
            }
            for row in cursor.fetchall()
        ]


        with open('./resources/EC_locations.json') as json_file:
            jsonLocalizaciones = json.load(json_file)

        # Crear el objeto JSON
        data = {
            "taxis": taxis,
            "clientes": clientes,
            "localizaciones": jsonLocalizaciones
        }

        # Convertir el objeto data a una cadena JSON con formato
        json_data = json.dumps(data, indent=4)

        return json_data
    except Exception as e:
        print(f"Error al exportar la base de datos: {e}")
        return None

    finally:
        # Cerrar la conexión a la base de datos
        conexion.close()

if __name__ == "__main__":
    print(exportDB())


### API
@app.route('/estadoActual-mapa', methods=['GET'])
def estadoActual():
    try:
        listado = exportDB()
        
        if listado:
            data = json.loads(listado)
            data["taxis"] = [taxi for taxi in data["taxis"] if taxi["estado"] != "desconectado"]
            listado = json.dumps(data, indent=4)
        
        if listado == None:
            return f"Error al obtener el estado actual del mapa.", 500
            
        return listado, 200
    except Exception as e:
        return f"Error al obtener el estado actual del mapa: {e}", 500


@app.route('/logs', methods=['GET'])
def obtenerLogs():
    fecha_actual = datetime.now().strftime("%Y-%m-%d")
    nombre_archivo = f"log/logs_{fecha_actual}.log"

    if os.path.exists(nombre_archivo):
        with open(nombre_archivo, "r") as archivo_log:
            contenido = archivo_log.read()
        return contenido, 200
    else:
        return "No hay logs disponibles para el día de hoy.", 404
    
if __name__ == "__main__":
    comprobarArgumentos(sys.argv)
    asignarConstantes(sys.argv)
    app.run(host=HOST, port=LISTEN_PORT, debug=True)