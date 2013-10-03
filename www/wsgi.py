from flask import Flask, render_template, request
from helper.db import DBHelper, DBSelect
from helper.filter import FilterHelper
from model.device import DeviceModel
from model.file import FileModel
import json
app = Flask(__name__)
app.debug = True

DBHelper('../data/index.db')
DeviceModel.install()
FileModel.install()
FilterHelper.install()

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
        if arg == 'device':
            models.add_filter(arg, {
                'in': args.get(arg).split(',')
            })
        else:
            FilterHelper.apply_filter(arg, args.get(arg).split(','), models)

    for model in models:
        try:
            data.append(json.dumps(model.get_data()))
        except UnicodeDecodeError:
            pass

    return '{"sql": %s, "files": [%s]}' % (
                json.dumps(models.render()), ','.join(data))

@app.route('/files/filters')
def file_filters_action():

    filters = FilterHelper.get_all_filters()

    device_opts = {}
    for device in DeviceModel.all():
        device_opts[device.id()] = device.product_name()
    if len(device_opts) > 1:
        filters.insert(0, {
            'label': 'Device',
            'multi': True,
            'param': 'device',
            'options': device_opts
        })

    return json.dumps({'filters': filters})

