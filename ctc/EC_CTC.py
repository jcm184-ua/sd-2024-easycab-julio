from flask import Flask, jsonify, request
import requests
import json
from api_openweather import API_KEY

app = Flask(__name__)

# Ruta del archivo JSON que contiene la ciudad
CITY_JSON_PATH = "city.json"

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
    app.run(debug=True)
