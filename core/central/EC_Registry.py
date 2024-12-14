import secrets
from flask import Flask, request, jsonify
from DB_CONNECTION import connDB
import os
from datetime import datetime
import sys

sys.path.append('../../shared')
from EC_Shared import *

app = Flask(__name__)

# Helper function
def obtenerIP(ID):
    try:
        with connDB() as conexionBBDD:
            cursor = conexionBBDD.cursor(dictionary=True)
            cursor.execute("SELECT IP FROM taxis WHERE id = %s", (ID,))

            resultado = cursor.fetchone()
            if resultado:
                return resultado['IP']
            else:
                printError(f"No se encontró IP para el ID {ID}.")
                return None
    except Exception as e:
        printError(f"Error al obtener IP: {e}")
        return None

def printLog(ID, message):
    IP = obtenerIP(ID)

    fecha_actual = datetime.now().strftime("%Y-%m-%d")
    nombre_archivo = f"log/logs_{fecha_actual}.log"
    os.makedirs(os.path.dirname(nombre_archivo), exist_ok=True)

    with open(nombre_archivo, "a") as archivo_log:
        archivo_log.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} [{IP}]- {message}\n")
        print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} [{IP}]- {message}")

@app.route("/registrar", methods=["PUT"])
def registrarTaxi():
    """
    Registra un taxi en el sistema y genera un token.
    """
    data = request.get_json()
    taxi_id = data.get("id")
    ip = request.remote_addr 

    if not taxi_id:
        return jsonify({"error": "ID del taxi es requerido"}), 400

    with connDB() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM taxis WHERE id = %s", (taxi_id,))
        if cursor.fetchone():
            return jsonify({"error": f"Taxi {taxi_id} ya está registrado"}), 409

        # Generar un token único para el taxi
        token = secrets.token_hex(16)

        cursor.execute("INSERT INTO taxis (id, token, IP) VALUES (%s, %s, %s)", 
                       (taxi_id, token, ip))
        conn.commit()

        printLog(taxi_id, f"Taxi {taxi_id} se ha registrado")

        return jsonify({"message": f"Registrado", "token": token}), 201

@app.route("/borrarTaxi/<taxi_id>", methods=["DELETE"])
def borrarTaxi(taxi_id):
    """
    Elimina el registro de un taxi del sistema.
    """
    with connDB() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM taxis WHERE id = %s", (taxi_id,))
        if not cursor.fetchone():
            return jsonify({"error": f"Taxi {taxi_id} no está registrado"}), 404

        printLog(taxi_id, f"Taxi {taxi_id} ha sido dado de baja")

        cursor.execute("DELETE FROM taxis WHERE id = %s", (taxi_id,))
        conn.commit()

        return jsonify({"message": f"Eliminado"}), 200

@app.route("/estado/<taxi_id>", methods=["GET"])
def verificarEstadoRegistro(taxi_id):
    """
    Verifica si un taxi está registrado en el sistema y devuelve su estado.
    """
    with connDB() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM taxis WHERE id = %s", (taxi_id,))
        taxi = cursor.fetchone()

        if taxi:
            return jsonify({"id": taxi["id"], "token": taxi["token"]}), 200
        return jsonify({"error": f"Taxi {taxi_id} no está registrado"}), 404

@app.route("/validar/<taxi_id>", methods=["POST"])
def validarToken(taxi_id):
    """
    Valida el token enviado por un taxi a la central.
    """
    data = request.get_json()
    token = data.get("token")

    if not token:
        return jsonify({"error": "Token es requerido"}), 400

    with connDB() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM taxis WHERE id = %s AND token = %s", (taxi_id, token))
        taxi = cursor.fetchone()

        if taxi:
            return jsonify({"message": "Token válido"}), 200
        return jsonify({"error": "Token inválido o taxi no registrado"}), 401

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5001)
