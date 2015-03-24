from __future__ import division
import uwsgi
import json
import re
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

# Start page route that redirects to login if box is on cloud
@app.route('/admin')
def admin_action():
	boxes = {}
	online = {}

	response = ""; 
	
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
		print "Error %d: %s" % (e.args[0],e.args[1])
	    
	finally:    
	        
	    if con:    
	        con.close()

	return render_template('admin.html', boxes=boxes, online=online)

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
	response = "" 
	PingModel.ping(request.args.get('local_ip'), request.remote_addr, request.args.get('uuid'), request.args.get('available_space'), request.args.get('used_space'), request.args.get('username'), request.args.get('devicecount'), request.args.get('cachecount'), request.args.get('temp'), request.args.get('software'))

	return "yes"