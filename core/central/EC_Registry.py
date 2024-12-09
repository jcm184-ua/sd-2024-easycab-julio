import secrets
from flask import Flask, request, jsonify
from DB_CONNECTION import connDB, init_db

app = Flask(__name__)

@app.route("/registrar", methods=["PUT"])
def registrarTaxi():
    """
    Registra un taxi en el sistema y genera un token.
    """
    data = request.get_json()
    taxi_id = data.get("id")

    if not taxi_id:
        return jsonify({"error": "ID del taxi es requerido"}), 400

    with connDB() as conn:
        cursor = conn.execute("SELECT * FROM taxis WHERE id = ?", (taxi_id,))
        if cursor.fetchone():
            return jsonify({"error": f"Taxi {taxi_id} ya está registrado"}), 409

        # Generar un token único para el taxi
        token = secrets.token_hex(16)

        conn.execute("INSERT INTO taxis (id, token) VALUES (?, ?)", 
                     (taxi_id, token))
        conn.commit()

        return jsonify({"message": f"Registrado", "token": token}), 201

@app.route("/borrarTaxi/<taxi_id>", methods=["DELETE"])
def borrarTaxi(taxi_id):
    """
    Elimina el registro de un taxi del sistema.
    """
    with connDB() as conn:
        cursor = conn.execute("SELECT * FROM taxis WHERE id = ?", (taxi_id,))
        if not cursor.fetchone():
            return jsonify({"error": f"Taxi {taxi_id} no está registrado"}), 404

        conn.execute("DELETE FROM taxis WHERE id = ?", (taxi_id,))
        conn.commit()
        return jsonify({"message": f"Eliminado"}), 200

@app.route("/estado/<taxi_id>", methods=["GET"])
def verificarEstadoRegistro(taxi_id):
    """
    Verifica si un taxi está registrado en el sistema y devuelve su estado.
    """
    with connDB() as conn:
        cursor = conn.execute("SELECT * FROM taxis WHERE id = ?", (taxi_id,))
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
        cursor = conn.execute("SELECT * FROM taxis WHERE id = ? AND token = ?", (taxi_id, token))
        taxi = cursor.fetchone()

        if taxi:
            return jsonify({"message": "Token válido"}), 200
        return jsonify({"error": "Token inválido o taxi no registrado"}), 401

if __name__ == "__main__":
    #init_db()  # Inicializa la base de datos si no existe
    app.run(debug=True, host="0.0.0.0", port=5001)