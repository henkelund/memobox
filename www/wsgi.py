from flask import Flask, render_template
from helper.db import DBHelper
from model.device import DeviceModel
app = Flask(__name__)

DBHelper('../data/index.db')
DeviceModel.install()

# Start page route
@app.route('/')
def index():
    devices = []
    for device in DeviceModel.all():
        devices.append(device.get_data())
    return render_template('index.html', devices=devices)

