import os
import time
import threading
import pickle
import requests
import numpy as np
from datetime import datetime
from flask import Flask, render_template, request
from tinydb import TinyDB

# ========== Configuration ==========
DB_PATH = "db.json"
ESP_ENDPOINT = "http://localhost:8091/"
DATA_FETCH_INTERVAL = 10  # seconds
DB_INSERT_INTERVAL = 60  # seconds
MODEL_PATH = "water_quality_model.pkl"
ENCODER_PATH = "label_encoder.pkl"

# ========== App Setup ==========
app = Flask(__name__)
db = TinyDB(DB_PATH)
current_directory = os.path.dirname(os.path.abspath(__file__))

# ========== Load Model & Encoder ==========
with open(os.path.join(current_directory, MODEL_PATH), "rb") as f:
    model = pickle.load(f)

with open(os.path.join(current_directory, ENCODER_PATH), "rb") as f:
    label_encoder = pickle.load(f)

# ========== Global Variables ==========
sensor_data = {
    "ph": "N/A",
    "tds": "N/A",
    "turbidity": "N/A",
    "water_level": "N/A",
    "usage_type": "N/A"
}

# ========== Helper Functions ==========

def get_water_usage_type(pH, TDS, Turbidity, Temperature):
    """Predict the usage type based on sensor input."""
    try:
        input_data = np.array([[pH, TDS, Turbidity, Temperature]])
        prediction = model.predict(input_data)
        return label_encoder.inverse_transform(prediction)[0]
    except Exception as e:
        print("Prediction error:", e)
        return "Unknown"

def get_last_10_data_from_db():
    """Fetch last 10 entries from the database."""
    try:
        data = db.all()
        return data[-10:] if len(data) > 10 else data
    except Exception as e:
        print("Error fetching data from DB:", e)
        return []

# ========== Background Tasks ==========

def upload_data_to_db():
    """Insert sensor data into DB at regular intervals."""
    while True:
        try:
            if sensor_data["ph"] != "N/A":
                db.insert({
                    "ph": str(sensor_data["ph"]),
                    "tds": str(sensor_data["tds"]),
                    "turbidity": str(sensor_data["turbidity"]),
                    "water_level": str(sensor_data["water_level"]),
                    "timestamp": datetime.now().strftime("%H:%M")
                })
        except Exception as e:
            print("Error uploading data to DB:", e)
        time.sleep(DB_INSERT_INTERVAL)

def fetch_data_from_esp():
    """Fetch sensor data from ESP8266."""
    global sensor_data
    while True:
        try:
            response = requests.get(ESP_ENDPOINT, timeout=5)
            if response.status_code == 200:
                values = response.text.strip().split(",")
                if len(values) == 4:
                    sensor_data["ph"] = float(values[0])
                    sensor_data["tds"] = float(values[1])
                    sensor_data["turbidity"] = float(values[2])
                    sensor_data["water_level"] = float(values[3])
                    sensor_data["usage_type"] = get_water_usage_type(
                        sensor_data["ph"],
                        sensor_data["tds"],
                        sensor_data["turbidity"],
                        35  # Default temperature
                    )
        except Exception as e:
            print("Error fetching data:", e)
        time.sleep(DATA_FETCH_INTERVAL)

# ========== Routes ==========

@app.route("/")
def index():
    return render_template("index.html", data=sensor_data)

@app.route("/predict", methods=["GET", "POST"])
def predict_model():
    if request.method == "GET":
        return render_template("predict.html")

    try:
        data = request.json
        label = get_water_usage_type(
            float(data["ph"]),
            float(data["tds"]),
            float(data["turbidity"]),
            float(data["temp"])
        )
        return {"data": label}
    except Exception as e:
        print("Prediction request failed:", e)
        return {"error": "Invalid input"}, 400

@app.route("/get_last_10_data", methods=["GET"])
def get_last_10_data():
    return {"data": get_last_10_data_from_db()}

# ========== Start Background Threads ==========
threading.Thread(target=fetch_data_from_esp, daemon=True).start()
threading.Thread(target=upload_data_to_db, daemon=True).start()

# ========== Run Server ==========
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8090, debug=False)
