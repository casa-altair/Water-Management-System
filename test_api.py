from flask import *
import random

def get_random_float(min_value=0.0, max_value=100.0):
    return str(round(random.uniform(min_value, max_value), 2))

app = Flask(__name__)

@app.route("/")
def home():
    """
    ph
    tds
    turbidity
    water_level
    """
    return f"{get_random_float()},{get_random_float()},{get_random_float()},{get_random_float()}"

app.run(host="localhost", port=8091, debug=False)