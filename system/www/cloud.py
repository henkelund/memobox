from __future__ import division
import uwsgi, json, os, re
import MySQLdb as mdb


#from dateutil.parser import parse
from datetime import date
from flask import Flask, session, render_template, request, jsonify, abort, Response, redirect, g, url_for
#from flask.ext.compress import Compress

# CSS & JS Compression lib
from flask.ext.assets import Environment, Bundle

# Box Helpers
from helper.db import DBHelper, DBSelect

# Box Models
from model.ping import PingModel
from model.message import MessageModel

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

# Creates DB Helper, loads config and determines wether box is local or cloud
@app.before_request
def before_request():
	if request.host == "www.sivula.se":
		g.username = "sari"
	elif request.host == "www.nordkvist.me":
		g.username = "nordkvist"
	elif not PingModel.validate_ip(request.host):
		g.username = request.base_url.split(".")[0].split("//")[1]
	else:
		g.username = None
		
	g.host = request.host
	g.islocalbox = False
	g.iscloudbox = not g.islocalbox
	g.localaccess = PingModel.haslocalaccess(request)

@app.route('/sendmessage')
def sendmessage_action():
	if request.args.get("reciever"):
		m = MessageModel(-1, MessageModel.get_box_by_uuid(request.args.get('username')), 1, int(request.args.get("type")), request.args.get("message"))
		m.send()
	return redirect("/admin?status=success")

# Start page route that redirects to login if box is on cloud
@app.route('/admin')
def admin_action():
	boxes = {}
	online = {}
	response = "" 
	status = False

	if request.args.get('status') > 0:
		status=True

	try:
	    con = mdb.connect('localhost', 'root', 'root', 'backupbox');
	    con.autocommit(True)
	    cur = con.cursor()
	    cur.execute("SELECT *, DATE_FORMAT(NOW(), '%s') - DATE_FORMAT(last_ping, '%s') as last_online FROM ping")
	    rows = cur.fetchall()

	    for row in rows:
			_rows = {}
			_rows['local_ip'] 		= row[0]
			_rows['public_ip'] 		= row[1]
			_rows['uuid'] 			= row[2]
			_rows['capacity'] 		= row[3]
			_rows['used_space'] 	= row[4]
			_rows['username'] 		= row[6]
			_rows['temp'] 			= row[7]
			_rows['software'] 		= row[8]
			_rows['last_online'] 	= row[13]
	    	
			pingdb = '/backups/'+_rows['username']+"/ping.db"
			userdb = '/backups/'+_rows['username']+"/index.db"
			
			_devices = {}
			DBHelper.initdb(userdb, True)
			device_list = DBSelect('device', ['serial', 'product_id', 'product_name', 'model', 'vendor_id', 'vendor_name', 'manufacturer', 'last_backup', 'state', 'new'] ).order("product_name", 'ASC').query()
			
			for rr in device_list:
					_raws = {}
					for raw in rr:
						_raws[raw] = str(rr[raw])
					_devices[_raws['serial']] = _raws
			
			_rows['devices'] = _devices

			boxes[_rows['username']] 	= _rows
			online[_rows['username']] 	= _rows['last_online']

	except mdb.Error, e:
		print "Error %d: %s" % (e.args[0], e.args[1])
	    
	finally:    
	        
	    if con:    
	        con.close()

	return render_template('admin.html', boxes=boxes, online=online, status=status)

# Start page route that redirects to login if box is on cloud
@app.route('/')
def index_action():
	config = DBHelper.loadconfig(g.username)
	ping = PingModel.lastping(g.username)

	if len(ping.keys()) > 0:
		_firstname = "debug" if not "FIRSTNAME" in config else config["FIRSTNAME"]
		_lastname = "debug" if not "LASTNAME" in config else config["LASTNAME"]
		return render_template('public.html', firstname=_firstname, lastname=_lastname, localaccess=int(g.localaccess), localip=ping["local_ip"])
	else:
		print "No user found"
		return render_template('nouser.html', username=str(g.username))

# Called by the local box client to send box information to the cloud software. Will never be used localy. 
@app.route('/ping')
def ping_action():
	_response = { "status" : "ok" }
	_messages = []
	PingModel.ping(request.args.get('local_ip'), request.remote_addr, request.args.get('uuid'), request.args.get('available_space'), request.args.get('used_space'), request.args.get('username'), request.args.get('devicecount'), request.args.get('cachecount'), request.args.get('temp'), request.args.get('software'))
	messages = MessageModel.load_messages(request.args.get('uuid'))

	for message in messages:
		_messages.append(message.values())
		message.mark_as_read()

	if len(_messages) > 0:
		_response["messages"] = _messages
	
	return jsonify(_response)


# Called by the local box client to send box information to the cloud software. Will never be used localy. 
@app.route('/messages')
def messages_action():
	messages = MessageModel.load_messages("");
	messages[0].mark_as_read()
	return jsonify(messages[0].values())

# Lets admin user acces log files on the cloud server
@app.route('/files/log/<display_name>')
def file_log_action(display_name=None):
	filename = os.path.abspath("/backups/"+DBHelper.loadconfig()["BOXUSER"]+"/public/log/"+display_name)	
	
	if not os.path.isfile(filename):
		abort(404)
	
	t = os.stat(filename)
	sz = str(t.st_size)
	
	_headers = {}	
	_headers['X-UA-Compatible'] = 'IE=Edge,chrome=1'
	_headers['Cache-Control'] = 'public, max-age=0'
	_headers["Content-Transfer-Enconding"] = "binary"
	_headers["Content-Length"] = sz
	mimetype = "text/plain"

	return Response(
				file(filename),
				headers=_headers,
				direct_passthrough=True,
				content_type=mimetype)