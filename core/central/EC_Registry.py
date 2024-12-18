import secrets
from flask import Flask, request, jsonify
import os
from datetime import datetime
import sys
import mariadb

sys.path.append('../../shared')
from EC_Shared import *

DATABASE_USER = 'ec_registry'
DATABASE_PASSWORD = 'sd2024_registry'

LISTEN_PORT = None

SERV_CERTIFICATE = './resources/certServ.pem'

app = Flask(__name__)

def comprobarArgumentos(argumentos):
    if len(argumentos) != 2:
        exitFatal("Necesito estos argumentos: <LISTEN_PORT>")
    printInfo("Número de argumentos correcto.")

def asignarConstantes(argumentos):
    global LISTEN_PORT
    LISTEN_PORT = int(argumentos[1])
    printInfo("Constantes asignadas.")

@app.route("/registrar/<taxi_id>", methods=["PUT"])
def registrarTaxi(taxi_id):
    """
    Registra un taxi en el sistema y devuelve un mensaje.
    """
    conexion, cursor = generarConexionBBDD(DATABASE_USER, DATABASE_PASSWORD)

    ip = request.remote_addr

    if not taxi_id:
        return jsonify({"error": "ID del taxi es requerido"}), 400

    # Verificar si el taxi ya está registrado
    cursor.execute("SELECT * FROM taxis WHERE id = %s", (taxi_id,))
    if cursor.fetchone():
        conexion.close()
        return jsonify({"error": f"Taxi {taxi_id} ya está registrado"}), 409

    # Insertar el nuevo taxi en la base de datos sin generar token
    cursor.execute("INSERT INTO taxis (id, IP) VALUES (%s, %s)", (taxi_id, ip))
    conexion.commit()
    conexion.close()

    printInfo(f"Taxi {taxi_id} se ha registrado")
    #printLog(taxi_id, f"Taxi {taxi_id} se ha registrado")

    return jsonify({"message": f"Taxi {taxi_id} registrado correctamente"}), 201

# FUNCIONA
@app.route("/borrarTaxi/<taxi_id>", methods=["DELETE"])
def borrarTaxi(taxi_id):
    """
    Elimina el registro de un taxi del sistema.
    """

    conexion, cursor = generarConexionBBDD(DATABASE_USER, DATABASE_PASSWORD)

    cursor.execute("SELECT * FROM taxis WHERE id = %s", (taxi_id,))
    if not cursor.fetchone():
        return jsonify({"error": f"Taxi {taxi_id} no está registrado"}), 404

    printInfo(f"Taxi {taxi_id} ha sido dado de baja")
    #printLog(taxi_id, f"Taxi {taxi_id} ha sido dado de baja")

    cursor.execute("DELETE FROM taxis WHERE id = %s", (taxi_id,))
    conexion.commit()
    conexion.close()

    return jsonify({"message": f"Eliminado"}), 200

@app.route("/estado/<taxi_id>", methods=["GET"])
def verificarEstadoRegistro(taxi_id):
    """
    Verifica si un taxi está registrado en el sistema y devuelve su estado.
    """

    conexion, cursor = generarConexionBBDD(DATABASE_USER, DATABASE_PASSWORD)

    cursor.execute("SELECT * FROM taxis WHERE id = %s", (taxi_id,))
    taxi = cursor.fetchone()

    conexion.close()
    if taxi:
        return jsonify({"id": taxi["id"], "token": taxi["token"]}), 200
    return jsonify({"error": f"Taxi {taxi_id} no está registrado"}), 404

if __name__ == "__main__":
    comprobarArgumentos(sys.argv)
    asignarConstantes(sys.argv)

    printInfo("Iniciando EC_Registry...")
    app.run(debug=True, port=LISTEN_PORT, ssl_context=(SERV_CERTIFICATE, SERV_CERTIFICATE))
