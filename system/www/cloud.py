from __future__ import division
import uwsgi
import math
import datetime as dt, time
import os
import json
import urllib, urllib2
import re
import uuid
import subprocess
import MySQLdb as mdb

from werkzeug import secure_filename

# Used to remove recursive directories
import shutil

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
from helper.access import AccessHelper

# Box Models
from model.device import DeviceModel
from model.box import BoxModel
from model.ping import PingModel
from model.file import FileModel

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

# Start page route that redirects to login if box is on cloud
@app.route('/admin')
def admin_action():
	boxes = {}
	online = {}

	response = ""; 
	
	try:
	    con = mdb.connect('localhost', 'root', 'root', 'backupbox');
	    cur = con.cursor()
	    cur.execute("SELECT * FROM ping")
	    rows = cur.fetchall()

	    for row in rows:
	    	response = response + str(row[0]) + ": "+ str(row[1]) + "<br />"

	except mdb.Error, e:
		print "Error %d: %s" % (e.args[0],e.args[1])
	    
	finally:    
	        
	    if con:    
	        con.close()
	
	return response
	
	for d in os.walk("/backups").next()[1]:
		pingdb = '/backups/'+d+"/ping.db"
		userdb = '/backups/'+d+"/index.db"
		if os.path.isfile(pingdb):
			try:
				_output = ""
				_output = _output + d
				_rows = {}
				DBHelper.initdb(pingdb, True)
				result = DBSelect('ping', ['last_ping', 'local_ip', 'public_ip', 'uuid', 'capacity', 'used_space', "strftime('%s','now') - strftime('%s', last_ping) as last_online", 'temp', 'software'] ).order("last_ping", 'DESC').limit(1).query()
				
				for r in result:
					for row in r:
						_rows[row] = str(r[row])
					online[d] = r["last_online"]
					
				_devices = {}
				DBHelper.initdb(userdb, True)
				device_list = DBSelect('device', ['serial', 'product_id', 'product_name', 'model', 'vendor_id', 'vendor_name', 'manufacturer', 'last_backup', 'state', 'new'] ).order("product_name", 'ASC').query()
				
				for rr in device_list:
						_raws = {}
						for raw in rr:
							_raws[raw] = str(rr[raw])
						_devices[_raws['serial']] = _raws
				
				_rows['devices'] = _devices
				boxes[d] = _rows
			except Exception as e:
				print e
	return render_template('admin.html', boxes=boxes, online=online)

# Start page route that redirects to login if box is on cloud
@app.route('/')
def index_action():
	return "forbidden"

# Called by the local box client to send box information to the cloud software. Will never be used localy. 
@app.route('/ping')
def ping_action():
	response = "" 
	PingModel.ping(request.args.get('local_ip'), request.args.get('public_ip'), request.args.get('uuid'), request.args.get('available_space'), request.args.get('used_space'), request.args.get('username'), request.args.get('devicecount'), request.args.get('cachecount'), request.args.get('temp'), request.args.get('software'))

	return "yes"

# Route for fetching last ping. Only used in cloud server. 
@app.route('/lastping')
def lastping():
		ping = PingModel.lastping(request.args.get('uuid'))
		return jsonify(ping)	