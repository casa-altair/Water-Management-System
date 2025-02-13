import os
from flask import Flask, render_template, request
import requests
import threading
# import mysql.connector
import time
import pickle
import numpy as np

# Flask app setup
app = Flask(__name__)
current_directory = os.path.dirname(os.path.abspath(__file__))

# ESP8266 server details (change ESP_IP to match your ESP8266)
ESP_IP = "http://192.168.4.1"  # ESP8266's local server IP
ESP_ENDPOINT = f"{ESP_IP}/"  # ESP8266 root URL

with open(f"{current_directory}/water_quality_model.pkl", "rb") as f:
    model = pickle.load(f)

with open(f"{current_directory}/label_encoder.pkl", "rb") as f:
    label_encoder = pickle.load(f)

# MySQL Database Connection
# db = mysql.connector.connect(
#     host="localhost",
#     user="root",      # Change to your MySQL username
#     password="root",  # Change to your MySQL password
#     database="water_quality"
# )

# cursor = db.cursor()
# cursor.execute("""
#     CREATE TABLE IF NOT EXISTS sensor_data (
#         id INT AUTO_INCREMENT PRIMARY KEY,
#         ph FLOAT,
#         tds FLOAT,
#         turbidity FLOAT,
#         water_level FLOAT,
#         timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
#     )
# """)
# db.commit()

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

                    api_data = get_water_usage_type(
                        sensor_data["ph"],
                        sensor_data["tds"],
                        sensor_data["turbidity"],
                        "35"
                    )
                    sensor_data["usage_type"] = api_data

                    # Insert into MySQL database
                    # cursor.execute("INSERT INTO sensor_data (ph, tds, turbidity, water_level) VALUES (%s, %s, %s, %s)",
                    # (sensor_data["ph"], sensor_data["tds"], sensor_data["turbidity"], sensor_data["water_level"]))
                    # db.commit()
        except Exception as e:
            print("Error fetching data:", e)
        
        time.sleep(10)  # Fetch data every 5 seconds

# Start the background thread
threading.Thread(target=fetch_data_from_esp, daemon=True).start()

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
    

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8090, debug=True)
