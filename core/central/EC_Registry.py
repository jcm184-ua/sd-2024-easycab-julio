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

app = Flask(__name__)

#NO FUNCIONA BIEN, NO TIENE QUE DEVOLVER TOKEN, SOLO AÑADIRLO A LA BBDD
""" PUT http://127.0.0.1:5001/registrar ->
<!doctype html>
<html lang=en>
<title>415 Unsupported Media Type</title>
<h1>Unsupported Media Type</h1>
<p>Did not attempt to load JSON data because the request Content-Type was not &#39;application/json&#39;.</p> """

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

# NO HAY QUE VALIDAR NADA. Los tokens son entre central y taxi
"""
@app.route("/validar/<taxi_id>", methods=["POST"])
def validarToken(taxi_id):
    #Valida el token enviado por un taxi a la central.
    
    data = request.get_json()
    token = data.get("token")

    if not token:
        return jsonify({"error": "Token es requerido"}), 400

    conexion, cursor = generarConexionBBDD(DATABASE_USER, DATABASE_PASSWORD)

    cursor.execute("SELECT * FROM taxis WHERE id = %s AND token = %s", (taxi_id, token))
    taxi = cursor.fetchone()

    conexion.close()
    if taxi:
        return jsonify({"message": "Token válido"}), 200
    return jsonify({"error": "Token inválido o taxi no registrado"}), 401
"""

if __name__ == "__main__":
    printInfo("Iniciando EC_Registry...")
    app.run(debug=True, host="0.0.0.0", port=5001)
