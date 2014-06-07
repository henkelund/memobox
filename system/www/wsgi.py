from __future__ import division
import uwsgi
import math
import datetime as dt, time
import os
from datetime import date
from subprocess import call
from datetime import date
from flask import Flask, render_template, request, jsonify, abort, Response, redirect
from helper.db import DBHelper, DBSelect
from helper.filter import FilterHelper
from helper.image import ImageHelper
from model.device import DeviceModel
from model.box import BoxModel
from model.ping import PingModel
from model.file import FileModel

ImageHelper('static/images', 'mint')
app = Flask(__name__)
app.debug = True
t = dt.datetime(2011, 10, 21, 0, 0)
now = dt.datetime.now()
b=BoxModel()

# Start page route
@app.route('/')
def index_action():
	PingModel.initdb(request.host, request.base_url)
	
	if PingModel.haslocalaccess(request):
		return redirect("http://"+PingModel.lastping()["local_ip"]+"/", code=302)
	else:
		return render_template('index.html', cloud=False)
		
@app.route('/files')
def files_action():
    PingModel.initdb(request.host, request.base_url)
    after = 1
    
    if (request.args.get('after') is not None) and (int(request.args.get('after')) > 0):
    	after = int(request.args.get('after'))
    
    data = []
    args = request.args
    pixel_ratio = 1
    cols = [
    '_id',
    'type',
    'subtype',
    'name'
    ]

    models = FileModel.all().join("file_thumbnail", "m._id = file_thumbnail.file").left_outer_join("file_attribute_text", "file_attribute_text.parent = m._id", "value").limit(32, (after-1)*32).where("width = 260").where("is_hidden = 0").order('m.created_at', "DESC")

    for arg in args.keys():
        vals = args.get(arg).split(',')
        
        if arg == 'year':
            st = dt.datetime(int(vals[0]), 1, 1)
            et = dt.datetime(int(vals[0]), 12, 31)
            starttime = time.mktime(st.timetuple())
            endtime = time.mktime(et.timetuple())
            models.where('m.created_at < ?', endtime)   
        elif (arg == 'format') and (len(vals) > 0) and (str(vals[0]) != "null"):
            print "Arg: "+arg
            print "Arg: "+str(vals[0])
            models.where("m.type = '"+str(vals[0])+"'")
        elif arg == 'device' and (len(vals) > 0) and vals[0] != "-1":
            models.where('m.device = '+str(vals[0]))

    print models.render()

    for model in models:
        data.append(model.get_data())

    return jsonify({'files': data, 'sql': models.render()})


@app.route('/info')
def file_info_action():
	with open ("/tmp/info.txt", "r") as myfile:
		data=myfile.read().replace('\n', '<br />')
	return data

@app.route('/ping')
def file_ping_action():
	PingModel.initdb(request.host, request.base_url)
	#try:
	PingModel.ping(request.args.get('local_ip'), request.args.get('public_ip'), request.args.get('uuid'), request.args.get('available_space'), request.args.get('used_space'), request.args.get('username'));
	#except:
	#    return "error"
	    
	return "ok"

@app.route('/device/update')
def file_devicedetail_action():
    PingModel.initdb(request.host, request.base_url)
    device = DeviceModel().load(str(request.args.get('id')))
    device.add_data({"product_name" : str(request.args.get('product_name'))})
    device.save()
    return "ok"

@app.route('/device/detail')
def file_deviceupdate_action():
    PingModel.initdb(request.host, request.base_url)
    device = DeviceModel().load(str(request.args.get('id')))
    return jsonify(device.get_data())

@app.route('/devices')
def file_devices_action():
    PingModel.initdb(request.host, request.base_url)
    devices = []
    for device in DeviceModel.all():
    	states = { -1 : 'Error', 1 : 'Preparing', 2 : 'Transfering files', 3 : 'Preparing images', 4 : 'Ready' }
    	images = DBSelect('file','count(*) as imagecount').join('device', 'device._id = file.device', None).where("device._id = "+str(device.id())).where("file.type = 'image'").query()
    	videos = DBSelect('file','count(*) as videocount').join('device', 'device._id = file.device', None).where("device._id = "+str(device.id())).where("file.type = 'video'").query()
    	thumbnails = DBSelect('file','count(*) as thumbnailcount').join('device', 'device._id = file.device', None).join('file_thumbnail', 'file_thumbnail.file = file._id', None).where("device._id = "+str(device.id())).where("file.type = 'image'").where("file_thumbnail.width = 260").query()
    			
    	imagecount = 0
    	videocount = 0
    	thumbnailcount = 0; 

    	for image in images:
    		imagecount = image['imagecount']
    	
    	for video in videos:
    		videocount = video['videocount']

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
            'videos': videocount,
            'thumbnails': thumbnailcount,
            'symbol': str(device.type()),
            'message': states[device.state()]
        })    

    return jsonify({'devices': devices})

@app.route('/files/details')
def file_details_action():
    PingModel.initdb(request.host, request.base_url)
    model = FileModel().load(request.args.get('id'))
    thumbnails = DBSelect('file').join('file_thumbnail', 'file._id = file_thumbnail.file', "thumbnail").where("file._id = "+str(request.args.get('id'))).where("file_thumbnail.width = 520").query()

    for thumbnail in thumbnails:
    	model.set_data('thumbnail', thumbnail["thumbnail"])

    devices = DBSelect('file').join('device', 'device._id = file.device', "product_name").where("file._id = "+str(request.args.get('id'))).query()

    for device in devices:
    	model.set_data('product_name', device["product_name"])
    
    	    
    return jsonify(model.get_data())

@app.route('/files/hide')
def file_hide_action():
	PingModel.initdb(request.host, request.base_url)
	if request.args.get('id') is None:
		return "error"
	DBSelect('file').where("file._id = "+str(request.args.get('id'))).query_update({'is_hidden': 1});
	return "ok"

@app.route('/files/calendar')
def file_calendar_action():
    PingModel.initdb(request.host, request.base_url)
    months = DBSelect('file',"strftime('%Y-%m', datetime(created_at, 'unixepoch')) as date").distinct(True).order('date','DESC')
    
    if request.args.get('device') is not None:
    	months.where("device = "+request.args.get('device'))
    
    months = months.query()
    
    _data = {}
    counter = 0
    
    for month in months:
    	print month["date"]
     	_data[counter] = month["date"]
     	counter = counter + 1
    
    return jsonify(_data)


@app.route('/files/stream/<file_id>/<display_name>/<type>/<size>')
def file_stream_action(file_id=None, display_name=None, type=None, size=None):
    PingModel.initdb(request.host, request.base_url)

    if not file_id:
        abort(404)

    model = FileModel().load(file_id);

    if not model.id():
        abort(404)

    if type == "thumbnail":
	    thumbnails = DBSelect('file_thumbnail').where("file = "+str(file_id)).where("width = "+size).query()
	    
	    for thumbnail in thumbnails:
	    	#thumbnail["thumbnail"]
	    	cache_dir = "/HDD/cache"
	    	
	    	if PingModel.islocal(request) == False:
	    		cache_dir = "/backups/"+request.base_url.split(".")[0].split("//")[1]+"/cache"
	    		print cache_dir
	    	
	    	filename = '%s/%s' % (cache_dir, thumbnail["thumbnail"])
	    	mimetype = '%s/%s' % (model.type(), model.subtype())
    else:    
	    filename = '%s/%s' % (model.abspath().replace("/backupbox/data", "/backups/"+request.base_url.split(".")[0].split("//")[1]), model.name())
	    mimetype = '%s/%s' % (model.type(), model.subtype())

    if not os.path.isfile(filename):
        abort(404)

    _headers = {}
    _headers['X-UA-Compatible'] = 'IE=Edge,chrome=1'
    _headers['Cache-Control'] = 'public, max-age=0'

    return Response(
                file(filename),
                headers=_headers,
                direct_passthrough=True,
                content_type=mimetype)