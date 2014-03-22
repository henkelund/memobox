from __future__ import division
import math
import datetime as dt, time
from flask import Flask, render_template, request, jsonify, abort, Response
#from flask_debugtoolbar import DebugToolbarExtension
from helper.db import DBHelper, DBSelect
from helper.filter import FilterHelper
from helper.image import ImageHelper
from model.device import DeviceModel
from model.file import FileModel
from datetime import date
from subprocess import call
import os

app = Flask(__name__)
app.debug = True
#app.logger.debug(""+tt)
t = dt.datetime(2011, 10, 21, 0, 0)
now=dt.datetime.now()
#toolbar = DebugToolbarExtension(app)

DBHelper('../../data/index.db')
ImageHelper('static/images', 'mint')
DeviceModel.install()
FileModel.install()
FilterHelper.install()

# Start page route
@app.route('/')
def index_action():
    return render_template('index.html')

@app.route('/files')
def files_action():

    if request.args.get('after', 0, type=int) == 0:
		return ""
	
    data = []
    args = request.args
    pixel_ratio = 1
    cols = [
    '_id',
    'type',
    'subtype',
    'name'
    ]

    models = FileModel.all().join("file_attribute_integer", "parent = m._id").columns(cols, "m", True).columns('value', 'file_attribute_integer').limit(16, (request.args.get('after', 0, type=int)-1)*16).where("file_attribute_integer.attribute = 5").order('file_attribute_integer.value', "DESC")

    for arg in args.keys():
        if arg == 'retina':
            val = args.get(arg)
            if val and val.lower() != 'false':
                pixel_ratio = 2
            continue

        vals = args.get(arg).split(',')

        #if arg == 'year':
        
        if arg == 'year':
            st = dt.datetime(int(vals[0]), 1, 1)
            et = dt.datetime(int(vals[0]), 12, 31)
            starttime = time.mktime(st.timetuple())
            endtime = time.mktime(et.timetuple())
            print(endtime)
            models.where('m.created_at < ?', endtime)   
        elif arg == 'format':
            formats = ['image','video','file']
            froms = formats[int(vals[0])]
            models.where('m.type = ?', froms)
        elif arg == 'device':
            models.add_filter(arg, {'in': vals})
            #models.where('m._id = ?',753)
        else:
            FilterHelper.apply_filter(arg, vals, models)

    ImageHelper().join_file_thumbnails(
        models,
        'm.%s' % FileModel._pk,
        260*pixel_ratio,
        260*pixel_ratio
    )

    ImageHelper().add_file_icons(models, 48*pixel_ratio, 128*pixel_ratio)
    for model in models:
        data.append(model.get_data())
    print models
    return jsonify({'files': data, 'sql': models.render()})

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

    return jsonify({'filters': filters})

@app.route('/files/devices')
def file_devices_action():

    devices = []
    for device in DeviceModel.all():
    	states = { -1 : 'Error', 1 : 'Preparing', 2 : 'Transfering files', 3 : 'Preparing images', 4 : 'Ready' }
    	images = DBSelect('device','count(*) as imagecount').join('file', 'device._id = file.device', None).where("device._id = "+str(device.id())).where("file.extension = 'jpg'").query()
    	thumbnails = DBSelect('device','count(*) as thumbnailcount').join('file', 'device._id = file.device', None).join('file_thumbnail', 'file_thumbnail.file = file._id', None).where("device._id = "+str(device.id())).where("file.extension = 'jpg'").query()

    	imagecount = 0
    	thumbnailcount = 0; 
    	
    	for image in images:
    		imagecount = image['imagecount']

    	for thumbnail in thumbnails:
    		thumbnailcount = thumbnail['thumbnailcount']

    	# Prepare status message
    	message = states[device.state()]+"<br /><br />"
    	
    	# If the number of images and thumbnails does not match, assume that thumbnails are still being generated and display progress
    	if(thumbnailcount != imagecount):
    		message = states[device.state()] + "<br />Progress: "+str(100-int(math.ceil(((imagecount-thumbnailcount)/imagecount)*100)))+"%"
    	
        devices.insert(0, {
            'id': device.id(),
            'product_name': device.product_name(),
            'state': device.state(),
            'model': device.model(),
            'product_id': device.product_id(),
            'last_backup': device.last_backup(),
            'images': imagecount,
            'images': thumbnailcount,
            'html': '<div id="'+str(device.id())+'" class="device"><div id="noti_Container"><img width="100" src="/static/images/icons/smartphone.png" /><div class="noti_bubble">'+str(imagecount)+'</div></div><a href="javascript:void(0);">'+device.product_name()+'</a><br />'+message+'</div>'
        })    

    return jsonify({'devices': devices})

@app.route('/files/details')
def file_details_action():

    model = FileModel().load(request.args.get('id'))
    return jsonify(model.get_data())

@app.route('/files/stream/<file_id>/<display_name>')
def file_stream_action(file_id=None, display_name=None):

    if not file_id:
        abort(404)

    model = FileModel().load(file_id)
    if not model.id():
        abort(404)

    filename = '%s/%s' % (model.abspath(), model.name())
    mimetype = '%s/%s' % (model.type(), model.subtype())

    if not os.path.isfile(filename):
        abort(404)

    return Response(
                file(filename),
                direct_passthrough=True,
                content_type=mimetype)

