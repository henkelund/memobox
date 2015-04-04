from __future__ import division
from werkzeug import secure_filename
import uwsgi, math, os, json, urllib, urllib2, re, uuid, subprocess
import datetime as dt, time

#from dateutil.parser import parse
from datetime import date
from subprocess import call
from datetime import date
from flask import Flask, session, render_template, request, jsonify, abort, Response, redirect, g, url_for
#from flask.ext.compress import Compress

# CSS & JS Compression lib
from flask.ext.assets import Environment, Bundle

# Box Helpers
from helper.db import DBHelper, DBSelect
from helper.filter import FilterHelper
from helper.image import ImageHelper
from helper.event import EventHelper

# Box Models
from model.device import DeviceModel
from model.box import BoxModel
from model.file import FileModel
from model.config import ConfigModel

ImageHelper('static/images', 'mint')

UPLOAD_FOLDER = '/tmp'
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])

# Initiate app and configure session key
app = Flask(__name__)
app.debug = True
app.secret_key = 'F12Zr47j\3yX R~X@H!jmM]Lwf/,?KT'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
#Compress(app)

# Initiate asset management(CSS & Javascript)
assets = Environment(app)

# Set up Box Model object
b=BoxModel()

# Creates DB Helper, loads config and determines wether box is local or cloud
@app.before_request
def before_request():
	if request.host == "www.sivula.se":
		g.username = "sari"
	elif request.host == "www.nordkvist.me":
		g.username = "nordkvist"
	elif not DBHelper.islocal() and not PingModel.validate_ip(request.host):
		g.username = request.base_url.split(".")[0].split("//")[1]
	else:
		g.username = DBHelper.loadconfig()["BOXUSER"]
		
	g.host = request.host
	g.islocalbox = DBHelper.islocal()
	g.iscloudbox = not g.islocalbox

	DBHelper.initdb()

	g.localaccess = False

# Start page route that redirects to login if box is on cloud
@app.route('/')
def index_action():
	DeviceModel.install()
	try:
		BoxModel.install()	
	except:
		pass
	
	try:
		ConfigModel.install()
	except: 
		pass
	
	BoxModel.init()		
	FileModel.install()
	FileModel.update()
	FilterHelper.install() 

	return render_template('index.html', username=g.username)

# Info route that displays box debug information. For administration use only
@app.route('/debug')
def debug_action():
	MESSAGE_TYPES = [
        "Information", 
        "Configuration",
        "Reboot", 
        "Shutdown"
    ]

	#f = ConfigModel.parse(None)
	#for message in f["messages"]:
	#	print MESSAGE_TYPES[int(message["type"])]
	
	#print ConfigModel.get_param("hello")
	EventHelper.parse_events("http://localhost/static/json.txt")
	#c = ConfigModel()
	#c.set_param("key", "uber"); 
	#c.set_param("value", "driver"); 
	#c.save()

	#params = ConfigModel.get_all_params()

	#for param in params:
	#	print param["key"]+"="+param["value"]

	return "Debug"

# Config route that loads session configuration 
@app.route('/config')
def config_action():
	config = DBHelper.loadconfig()
	config.pop("LOCAL", None)
	config.pop("BOXUSER", None)
	config["USERNAME"] = g.username
	config["ISLOCAL"] = g.islocalbox

	if os.path.isfile("../data/public/_publish"):
		config["PENDING_PUBLISH"] = "true"
	else:
		config["PENDING_PUBLISH"] = "false"

	return jsonify(config)

# Config route that loads session configuration 
@app.route('/config/save')
def config_save_action():
	config = DBHelper.loadconfig()

	for key in request.args.keys():
		if key.upper() in config:
			config[key.upper()] = request.args.get(key)

	DBHelper.saveconfig(config)

	return jsonify(config)


# Display login page
@app.route('/login')
def login_action():
	if request.args.get('password') == DBHelper.loadconfig(AccessHelper.requestuser(request.base_url))["PASSWORD"]:
		session["verified_"+AccessHelper.requestuser(request.base_url)] = True
		return redirect("/")
	elif request.args.get('password') != DBHelper.loadconfig(AccessHelper.requestuser(request.base_url))["PASSWORD"]:
		return render_template('public.html', message="Ops! Wrong password.", firstname=DBHelper.loadconfig()["FIRSTNAME"], lastname=DBHelper.loadconfig()["LASTNAME"])
	else:
		return render_template('public.html', firstname=DBHelper.loadconfig()["FIRSTNAME"], lastname=DBHelper.loadconfig()["LASTNAME"])
		
# Route that loads next page of files
@app.route('/files')
def files_action():
	after = 1
	
	# Read requested page if available
	if (request.args.get('after') is not None) and (int(request.args.get('after')) > 0):
		after = int(request.args.get('after'))
	
	# Object that holds image/file information
	data = []
	
	# Request parameters
	args = request.args
	pixel_ratio = 1
	cols = [
	'_id',
	'type',
	'subtype',
	'name'
	]

	# Determines wether request contains only media files or documents
	isMedia = True

	models = FileModel.all().columns(["_id", "created_at", "type", "name"], None, True).join("device", "m.device = device._id", ["locked", "product_name"]).add_attribute("duration").where("is_hidden = 0").order('m.created_at', "DESC")

	for arg in args.keys():
		vals = args.get(arg).split(',')
		
		if arg == 'mode':
			models = FileModel.all().add_filter("published",  {'eq': (1)}).add_attribute("description").add_attribute("uuid").where("is_hidden = 0").order('m.created_at', "DESC")
		if arg == 'year':
			st = dt.datetime(int(vals[0]), 1, 1)
			et = dt.datetime(int(vals[0]), 12, 31)
			starttime = time.mktime(st.timetuple())
			endtime = time.mktime(et.timetuple())
			models.where('m.created_at < ?', endtime)   
		elif (arg == 'format') and (len(vals) > 0) and (str(vals[0]) != "null") and (str(vals[0]) != ""):
			if str(vals[0]) == "other":
				models.where("m.type not in ('image', 'video')").limit(1000, (after-1)*1000)
				isMedia = False
			else:
				sql = "m.type IN (%s)"
				_vals = ""

				for value in vals:
				        _vals = _vals + "'"+value+"'"
				        if vals[-1] != str(value):
				                _vals = _vals + ","

				models.where(sql % _vals)

		elif arg == 'device' and (len(vals) > 0) and vals[0] != "-1":
			models.where('m.device in ('+str(vals[0])+')')
		elif arg == 'daterange' and (len(vals) > 0) and vals[0] != "undefined" and vals[0] != "null":
			models.where("strftime('%Y-%m', datetime(created_at, 'unixepoch')) = '"+str(vals[0])+"'")

	if isMedia:
		models.where("width = 260").join("file_thumbnail", "m._id = file_thumbnail.file").limit(32, (after-1)*32)

	for model in models:
		#model.
		data_list = model.get_data()
		for key, value in data_list.items():
			if key == "name" or key == "thumbnail":
				new_value = value.decode('unicode-escape')
				data_list[key] = new_value
				#data_list[key] = value.decode('iso-8859-1')
		
		data.append(data_list)
	
	return jsonify({'files': data})

# Info route that displays box debug information. For administration use only
@app.route('/info')
def info_action():
	#print os.path.abspath('../../data')
	config = DBHelper.loadconfig()
	config_output = ""
	if not os.path.isfile("/tmp/info.txt"):
		subprocess.call(['../bin/gatherData.sh'])

	with open ("/tmp/info.txt", "r") as myfile:
		data=myfile.read().replace('\n', '<br />')

	for key, value in config.iteritems():
		config_output += key+"="+value+"<br />"

	message = ""
	if request.args.get('message') is not None:
		message = request.args.get('message')
	
	return render_template('info.html', config=config_output, info=data, message=message)

# Route for displaying configuration file edit form
@app.route('/configuration/edit')
def configuration_edit_action():
	config = DBHelper.loadconfig()
	return render_template('edit.html', config=config)

# Route for saving configuration parameters
@app.route('/configuration/save')
def configuration_save_action():
	output = ""
	conf = {}

	for key, value in request.args.iteritems():
		if key.startswith("config_"):
			conf[key[7:]] = value

	new_config = DBHelper.saveconfig(conf)
	return redirect("/info?message=Configuration has been saved")

# Dangerous route that erases an entire box. Use carefully...
@app.route('/box/erase')
def box_erase_action():
	folders = ['../../data/cache/thumbnails', '../../data/devices', '../../data/index.db' ]
	for folder in folders:
		try:
			if(os.path.isdir(folder)):
				shutil.rmtree(folder)
			else:
				os.remove(folder)
		except Exception as e:
			print e

	return redirect("/")

# Route for publishing images and files on cloud server
@app.route('/upload')
def upload_action():
	config = DBHelper.loadconfig()
	files = request.args.get("files").split(",")

	for f in files:
		_file = FileModel().load(f)
		ff = str(_file.abspath()+"/"+_file.name())
		uid = str(uuid.uuid1())+'.jpg'
		shutil.copyfile(ff, "../data/public/"+uid)

		#if request.args.get("description-"+f):
		#	_file.description(request.args.get("description-"+f));

		_file.published(1)
		_file.uuid(uid)
		_file.save()
	
	open("../data/public/_publish", 'a').close()
		
	return "ok"

# Used to change the name of a backup device
@app.route('/device/update')
def device_update_action():
	device = DeviceModel().load(str(request.args.get('id')))
	device.add_data({"product_name" : str(request.args.get('product_name'))})
	device.add_data({"password" : str(request.args.get('password'))})
	device.add_data({"type" : str(request.args.get('type'))})
	device.add_data({"new" : 0})
	device.save()
	return "ok"

# Used to change the name of a backup device
@app.route('/device/state/update')
def device_state_update_action():
	device = DeviceModel().load(str(request.args.get('id')), "serial")
	device.add_data({"state" : int(request.args.get('state'))})
	device.save()
	return "ok"

# Used to change the name of a backup device
@app.route('/device/erase')
def device_erase_action():
	device = DeviceModel().load(str(request.args.get('id')))
	device_data = device.get_data();

	folder = '../../data/devices/'+device_data["serial"]

	try:
		if(os.path.isdir(folder)):
			shutil.rmtree(folder)
		else:
			os.remove(folder)
	except Exception as e:
		print e

	device.delete()

	return "ok"


# Retreivs information about a device
@app.route('/device/detail')
def device_detail_action():
	device = DeviceModel().load(str(request.args.get('id')))
	device_data = device.get_data();
	device_data["image_count"] = DeviceModel().image_count(str(request.args.get('id')));
	device_data["video_count"] = DeviceModel().video_count(str(request.args.get('id')));
	device_data["last_backup"] = DeviceModel().last_backup(str(request.args.get('id')));
	return jsonify(device.get_data())

# Gets a list of, and information about, all available devices. Used to populate navigation bar. 
@app.route('/device/list')
def file_devices_action():
	devices = []
	
	for device in DeviceModel.all():
		states = { -1 : 'Error', 1 : 'Preparing', 2 : 'Transfering files', 3 : 'Preparing images', 4 : 'Ready' }
		formats = ['image', 'video', 'other' ]
		count = {}
		images = 0
		videos = 0
		documents = 0
		date_range = {}
		typecount = {}

		backups = device.get_backups()
		date_range = device.get_daterange(device.id())
		typecount = device.get_typecount(device.id())
		
		if "image" in typecount:
			images = typecount["image"]

		if "video" in typecount:
			videos = typecount["video"]

		if "all" in typecount:
			documents = typecount["all"] - images - videos

		devices.insert(0, {
			'id': device.id(),
			'new': device.new(),
			'password': device.password(),
			'product_name': device.product_name(),
			'state': device.state(),
			'type': device.type(),
			'model': device.model(),
			'product_id': device.product_id(),
			'last_backup': DeviceModel().last_backup(str(device.id())),
			'images': images,
			'videos': videos,
			'others': documents,
			'serial': device.serial(),
			'backups': backups,
			'range': date_range,
			'symbol': str(device.type())
		})    
		
	if len(devices) > 0:
		devices.insert(0, {
			'id': -1,
			'images': device.get_typecount(-1)["images"],
			'videos': device.get_typecount(-1)["videos"],
			'others': device.get_typecount(-1)["documents"],
			'range': device.get_daterange(-1)
			});

	return jsonify({'devices': devices})

# Get detailed information about a file object
@app.route('/files/details')
def file_details_action():
	data = []
	model = FileModel().load(request.args.get('id'))
	thumbnails = DBSelect('file').join('file_thumbnail', 'file._id = file_thumbnail.file', "thumbnail").where("file._id = "+str(request.args.get('id'))).where("file_thumbnail.width = 520").query()

	for thumbnail in thumbnails:
		model.set_data('thumbnail', thumbnail["thumbnail"])

	devices = DBSelect('file').join('device', 'device._id = file.device', "product_name").where("file._id = "+str(request.args.get('id'))).query()

	for device in devices:
		model.set_data('product_name', device["product_name"])

	data_list = model.get_data()
	for key, value in data_list.items():
		if key == "name" or key == "thumbnail":
			new_value = value.decode('unicode-escape')
			data_list[key] = new_value
			#data_list[key] = value.decode('iso-8859-1')
			
	return jsonify(data_list)

# Hidess a file on the box. The file is not deleted, only unpublished. 
@app.route('/files/hide')
def file_hide_action():
	if request.args.get('id') is None:
		return "error"
	DBSelect('file').where("file._id = "+str(request.args.get('id'))).query_update({'is_hidden': 1});
	return "ok"

# Uses pwinty API to order photo copies of photos. 
@app.route('/print')
def print_action():
	files = request.args.get("files").split(",")
	orderitems = {}

	ftp = FTP('nordkvist.backupbox.se')     # connect to host, default port
	ftp.login()
	ftp.cwd('incoming')


	pwinty.apikey = "0537a38f-d2b4-4360-842d-e254a7161128"
	pwinty.merchantid = "2260a6b6-f261-4e86-8f18-81597a3637f6"

	countries = {
	"AT": "Austria",
	"AU": "Australia",
	"BE": "Belgium",
	"BR": "Brazil",
	"CA": "Canada",
	"CH": "Switzerland",
	"CL": "Chile",
	"DE": "Germany",
	"DK": "Denmark",
	"ES": "Spain",
	"FR": "France",
	"GB": "United Kingdom",
	"IE": "Ireland",
	"IT": "Italy",
	"MX": "Mexico",
	"NL": "Netherlands",
	"ES": "Spain",
	"SE": "Sweden",
	"US": "United States",
	}

	order = pwinty.Order.create(
		recipient_name =            request.args.get("recipient_name"),
		address_1 =                 request.args.get("address_1"),
		address_2 =                 '',
		address_town_or_city =      request.args.get("address_town_or_city"),
		state_or_county =           countries[request.args.get("country")],
		postal_or_zip_code =        request.args.get("postal_or_zip_code"),
		destination_country_code =  request.args.get("country"),
		country_code =              request.args.get("country"),
		qualityLevel =              'Standard'
	)

	for f in files:
		_file = FileModel().load(f)
		ff = str(_file.abspath()+"/"+_file.name())
		uid = str(uuid.uuid1())+'.jpg'
		
		if _file.width() > _file.height():
			cmdline = [
				'gm',
				'convert',
				'-rotate',
				'90',
				ff,
				"/tmp/"+uid
			]                   
				
			subprocess.call(cmdline)
			ff = "/tmp/"+uid

		orderitems[uid] = ff
		ftp.storbinary('STOR '+uid, open(ff, 'rb'))
		
		photo = order.photos.create(
			type =      '13x19_cm',
			url =       'http://nordkvist.backupbox.se/static/pwinty/'+uid,
			copies =    '1',
			sizing =    'Crop'
		)

	order_status = order.get_submission_status()

	if not order_status.is_valid:
		return "error"
	else:
		order.submit()
		return str(order_status.id)

# Gets icon for a file
@app.route('/icon/<type>')
def icon_action(type=None):
	
	if os.path.isfile("static/images/icons/mint/48/"+type+".png"):
		return redirect("/static/images/icons/mint/48/"+type+".png")
	else:
		return redirect("/static/images/icons/mint/48/unknown.png")

# Get thumbnails on the box
@app.route('/file/thumbnail/<size>/<file_id>')
def file_thumbnail_action(size=None, file_id=None):
	_size = 260
	if not file_id:
		abort(404)

	model = FileModel().load(file_id);
	filename = ""

	if not model.id():
		abort(404)

	if size == "medium":
		_size = 520

	thumbnails = DBSelect('file_thumbnail').where("file = "+str(file_id)).where("width = " + str(_size)).query()
	
	for thumbnail in thumbnails:
		filename = '%s/%s' % ("/static/cache", urllib.quote(thumbnail["thumbnail"]))
		return redirect(filename)

	abort(404)		

# View full version of file
@app.route('/file/view/<file_id>')
def file_view_action(file_id=None):
	if not file_id:
		abort(404)

	model = FileModel().load(file_id);
	filename = ""

	if not model.id():
		abort(404)

	filename = '%s/%s' % ("/static"+model.abspath().replace("/backupbox/data", ""), urllib.quote(model.name()))
	return redirect(filename)

# Download full files
@app.route('/file/download/<file_id>')
def file_download_action(file_id=None):
	_headers = {}	

	if not file_id:
		abort(404)

	model = FileModel().load(file_id);
	filename = ""

	if not model.id():
		abort(404)

	filename = '%s/%s' % (model.abspath(), model.name())
	_headers["Content-Disposition"] = "attachment; filename="+model.name()
	mimetype = '%s/%s' % (model.type(), model.subtype())

	if not os.path.isfile(filename):
		abort(404)
	
	t = os.stat(filename)
	sz = str(t.st_size)

	_headers['X-UA-Compatible'] = 'IE=Edge,chrome=1'
	_headers['Cache-Control'] = 'public, max-age=0'
	_headers["Content-Transfer-Enconding"] = "binary"
	_headers["Content-Length"] = sz

	return Response(
				file(filename),
				headers=_headers,
				direct_passthrough=True,
				content_type=mimetype)

# Get profile image
@app.route('/file/profile')
def file_profile_action():
	_headers = {}	

	public_filename = os.path.abspath("/backups/"+DBHelper.loadconfig()["BOXUSER"]+"/cache/profile.jpg")
	local_filename = os.path.abspath("/HDD/cache/profile.jpg")

	if os.path.isfile(public_filename):
		filename = public_filename
	elif os.path.isfile(local_filename):
		filename = local_filename
	else:
		filename = os.path.abspath("static/images/profile.jpg");

	mimetype = "image/jpeg"

	
	if not os.path.isfile(filename):
		abort(404)
	
	t = os.stat(filename)
	sz = str(t.st_size)

	_headers['X-UA-Compatible'] = 'IE=Edge,chrome=1'
	_headers['Cache-Control'] = 'public, max-age=0'
	_headers["Content-Transfer-Enconding"] = "binary"
	_headers["Content-Length"] = sz

	return Response(
				file(filename),
				headers=_headers,
				direct_passthrough=True,
				content_type=mimetype)


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

@app.route('/profileupload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        file = request.files['file']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            _width = 160
            _height = 160

            cmdline = [
            	'gm',
            	'convert',
            	'-size',
            	str(_width)+"x"+str(_height),
            	os.path.join(app.config['UPLOAD_FOLDER'], filename),
            	'-thumbnail',
            	str(_width)+"x"+str(_height)+"^",
            	'-gravity',
            	'center',
            	'-extent',
            	str(_width)+"x"+str(_height),
            	'+profile',
            	'"*"',
            	'-auto-orient',
            	'/HDD/cache/profile.jpg'
            	]                 	
            	
            print " ".join(cmdline)
            subprocess.call(cmdline)

            # Write flag to public-dir in order to perform file upload
            open("../data/public/_publish", 'a').close()
            return "ok"
