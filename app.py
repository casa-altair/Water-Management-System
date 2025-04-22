import os
from flask import Flask, render_template, request
import requests
import threading
# import mysql.connector
from tinydb import TinyDB, Query
import time
import pickle
import numpy as np
from datetime import datetime

db = TinyDB('db.json')


# Flask app setup
app = Flask(__name__)
current_directory = os.path.dirname(os.path.abspath(__file__))

ESP_ENDPOINT = "http://192.168.4.1/"
# ESP_ENDPOINT = "http://localhost:8091/"

with open(f"{current_directory}/water_quality_model.pkl", "rb") as f:
    model = pickle.load(f)

with open(f"{current_directory}/label_encoder.pkl", "rb") as f:
    label_encoder = pickle.load(f)


# Store sensor data globally
sensor_data = {
    "ph": "N/A",
    "tds": "N/A",
    "turbidity": "N/A",
    "water_level": "N/A",
    "usage_type": "N/A"
}

def get_water_usage_type(pH, TDS, Turbidity, Temperature):
    input_data = np.array([[pH, TDS, Turbidity, Temperature]])
    prediction = model.predict(input_data)
    predicted_label = label_encoder.inverse_transform(prediction)[0]
    return predicted_label

def get_last_10_data_from_db():
    try:
        data = db.all()
        if len(data) > 10:
            data = data[-10:]
        return data
    except Exception as e:
        print("Error fetching data from DB:", e)
        return []
    

def uplload_data_to_db():
    while True:
        try:
            if sensor_data["ph"] != "N/A":
                print(sensor_data)

                db.insert( {
                            "ph": str(sensor_data["ph"]),
                            "tds": str(sensor_data["tds"]),
                            "turbidity": str(sensor_data["turbidity"]),
                            "water_level": str(sensor_data["water_level"])
                        })
                time.sleep(60)

        except Exception as e:
            print("Error uploading data to DB:", e)


# Function to fetch data from ESP8266
def fetch_data_from_esp():
    global sensor_data
    while True:
        try:
            response = requests.get(ESP_ENDPOINT, timeout=5)
            if response.status_code == 200:
                data = response.text.strip().split(",")  # Assuming ESP sends CSV format
                if len(data) == 4:
                    sensor_data["ph"] = float(data[0])
                    sensor_data["tds"] = float(data[1])
                    sensor_data["turbidity"] = float(data[2])
                    sensor_data["water_level"] = float(data[3])

                    api_data = get_water_usage_type( sensor_data["ph"], sensor_data["tds"], sensor_data["turbidity"], "35" )
                    sensor_data["usage_type"] = api_data

        except Exception as e:
            print("Error fetching data:", e)
        
        time.sleep(10)  # Fetch data every 5 seconds

# Start the background thread
threading.Thread(target=fetch_data_from_esp, daemon=True).start()
threading.Thread(target=uplload_data_to_db, daemon=True).start()

@app.route('/')
def index():
    return render_template("index.html", data=sensor_data)

@app.route("/predict", methods=["get", "post"])
def predict_model():
    if request.method.lower() == "get":
        return render_template("predict.html")
    data = request.json
    print(data)
    predicted_label = get_water_usage_type(
        data["ph"], data["tds"], data["turbidity"], data["temp"]
    )
    print(predicted_label)
    return {"data": predicted_label}

print(get_last_10_data_from_db())

@app.route("/get_last_10_data", methods=["get"])
def get_last_10_data():
    data = get_last_10_data_from_db()
    return {"data": data}

if __name__ == '__main__':
    app.run( host='0.0.0.0', port=8090, debug=False )
