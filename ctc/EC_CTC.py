from flask import Flask, jsonify
import requests
import json
import sys
from api_openweather import API_KEY

sys.path.append('../shared')
from EC_Shared import *

app = Flask(__name__)

LISTEN_PORT = None

# Ruta del archivo JSON que contiene la ciudad
CITY_JSON_PATH = "city.json"

def comprobarArgumentos(argumentos):
    if len(argumentos) != 2:
        exitFatal("Necesito estos argumentos: <LISTEN_PORT>")
    printInfo("Número de argumentos correcto.")

def asignarConstantes(argumentos):
    global LISTEN_PORT
    LISTEN_PORT = int(argumentos[1])
    printInfo("Constantes asignadas.")

# Leer la ciudad desde el archivo JSON
def leerCiudad():
    with open(CITY_JSON_PATH, "r") as file:
        data = json.load(file)
        return data.get("city", "Unknown")

# Consultar el clima desde OpenWeather
def obtenerClima(city):
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&units=metric&appid={API_KEY}"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        return data.get("main", {}).get("temp")
    else:
        return None

# API para obtener el estado del tráfico
@app.route("/consultarClima", methods=["GET"])
def consultarClima():
    while True:
        city = leerCiudad()
        temperature = obtenerClima(city)

        if temperature is None:
            return jsonify({"status": "KO", "message": "Error al obtener el clima"}), 500

        if temperature < 0:
            return jsonify({"status": "KO", "message": f"Circulación no viable en {city}. Temperatura: {temperature}°C"})
        else:
            return jsonify({"status": "OK", "message": f"Circulación viable en {city}. Temperatura: {temperature}°C"})


if __name__ == "__main__":
    comprobarArgumentos(sys.argv)
    asignarConstantes(sys.argv)
    app.run(debug=True, host='0.0.0.0', port=LISTEN_PORT)
