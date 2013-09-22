from flask import Flask, render_template, request
from helper.db import DBHelper, DBSelect
from model.device import DeviceModel
from model.file import FileModel
import json
app = Flask(__name__)
app.debug = True

DBHelper('../data/index.db')

# Start page route
@app.route('/')
def index_action():
    return render_template('index.html')

@app.route('/files')
def files_action():

    data = []
    args = request.args
    models = FileModel.all().limit(48)

    for arg in args.keys():
        models.add_filter(arg, {
            'in': args.get(arg).split(',')
        })

    for model in models:
        try:
            data.append(json.dumps(model.get_data()))
        except UnicodeDecodeError:
            pass

    return '{"sql": %s, "files": [%s]}' % (
                json.dumps(models.render()), ','.join(data))

@app.route('/files/filters')
def file_filters_action():

    filters = []

    device_opts = {}
    for device in DeviceModel.all():
        device_opts[device.id()] = device.product_name()
    if len(device_opts) > 1:
        filters.append({
            'label': 'Device',
            'multi': True,
            'param': 'device',
            'options': device_opts
        })

    type_opts = {}
    type_select = DBSelect(FileModel().get_table(), ('type')).distinct(True);
    for file_type in type_select.query().fetchall():
        type_opts[file_type['type']] = file_type['type'].capitalize()
    if len(type_opts) > 1:
        filters.append({
            'label': 'Type',
            'multi': True,
            'param': 'type',
            'options': type_opts
        })

    return json.dumps({'filters': filters})

