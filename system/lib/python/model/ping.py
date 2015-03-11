import subprocess
import MySQLdb as mdb
from base import BaseModel
from helper.db import DBHelper, DBSelect
from helper.filter import FilterHelper
from model.device import DeviceModel
from model.box import BoxModel
from model.file import FileModel
from flask import g, jsonify

class PingModel(BaseModel):
    """Model describing a box system info"""

    @staticmethod
    def install():
        """Define install routines for this model"""
        return (
            DBHelper().query(
                """
                    CREATE TABLE ping (
                        "_id"          INTEGER PRIMARY KEY AUTOINCREMENT,
                        "local_ip"     TEXT NOT NULL DEFAULT '',
                        "public_ip"    TEXT NOT NULL DEFAULT '',
                        "uuid"         TEXT NOT NULL DEFAULT '',
                        "capacity"     TEXT NOT NULL DEFAULT '',
                        "used_space"   TEXT NOT NULL DEFAULT '', 
                        "last_ping"	   DATETIME, 
                        "username"     TEXT NOT NULL DEFAULT '', 
                        "temp"     	   TEXT NOT NULL DEFAULT '', 
                        "software"     	   TEXT NOT NULL DEFAULT '', 
                        "devicecount"  INT, 
                        "cachecount"   INT,
                        "remote_devicecount"  INT, 
                        "remote_cachecount"   INT
                    )
                """)
        )
    @staticmethod
    def ping(local_ip, public_ip, uuid, capacity, used_space, username, devicecount, cachecount, temp, software):
		config = DBHelper.loadconfig()

		# Count files in cache folder
		find = subprocess.Popen(['find', '/backupbox/data/cache', '-type', 'f'],stdout=subprocess.PIPE)
		wc = subprocess.Popen(['wc', '-l'], stdin = find.stdout, stdout=subprocess.PIPE)
		remote_cachecount = wc.stdout.readline().replace("\\n", "")

		# Count files in cache folder
		find = subprocess.Popen(['find', '/backupbox/data/devices', '-type', 'f'],stdout=subprocess.PIPE)
		wc = subprocess.Popen(['wc', '-l'], stdin = find.stdout, stdout=subprocess.PIPE)
		remote_devicecount = wc.stdout.readline().replace("\\n", "")

		con = None
		print "Start"

		try:
			con = mdb.connect('localhost', 'root', 'root', 'backupbox');
			cur = con.cursor()
			cur.execute("SELECT count(*) as pingcount FROM ping WHERE uuid = '"+uuid+"'")
			rows = cur.fetchall()
			pingcount = 0;

			for row in rows:
				pingcount = row[0];

			if pingcount == 0:
				cur.execute(
			                """
			                    INSERT INTO ping (local_ip, public_ip, uuid, capacity, used_space, last_ping, username, devicecount, cachecount, remote_devicecount, remote_cachecount, temp, software) VALUES("%s", "%s", "%s", "%s", "%s", NOW(), "%s", "%s", "%s", "%s", "%s", "%s", "%s")
			                """ % (local_ip, public_ip, uuid, capacity, used_space, username, devicecount, cachecount, remote_devicecount, remote_cachecount, temp, software))
				con.commit()
			else:
			     cur.execute(
			                """
			                    UPDATE ping SET local_ip = "%s", public_ip = "%s", capacity = "%s", used_space = "%s", last_ping = NOW(), username = "%s", devicecount = "%s", cachecount = "%s", remote_devicecount = "%s", remote_cachecount = "%s", temp = "%s", software = "%s" WHERE uuid = "%s"
			                """ % (local_ip, public_ip, capacity, used_space, username, devicecount, cachecount, remote_devicecount, remote_cachecount, temp, software, uuid))
			     con.commit()

		except mdb.Error, e:
			print "Error %d: %s" % (e.args[0],e.args[1])

		finally:    
			if con:    
			    con.close()

    @staticmethod
    def lastping( uuid ):
		_ping = {}
		con = None

		try:
			con = mdb.connect('localhost', 'root', 'root', 'backupbox');
			cur = con.cursor()
			cur.execute("SELECT * FROM ping WHERE uuid = '%s'" % (uuid))
			rows = cur.fetchall()
			pingcount = 0;

			for row in rows:
				_ping["local_ip"] = row[0]
				_ping["public_ip"] = row[1]
				_ping["uuid"] = row[2]
				_ping["capacity"] = row[3]
				_ping["used_space"] = row[4]
				_ping["last_ping"] = str(row[5])
				_ping["username"] = row[6]
				_ping["devicecount"] = row[9]
				_ping["cachecount"] = row[10]
				_ping["remote_devicecount"] = row[11]
				_ping["remote_cachecount"] = row[12]

		except mdb.Error, e:
			print "Error %d: %s" % (e.args[0],e.args[1])

		finally:    
			if con:    
			    con.close()

		return _ping

    @staticmethod
    def validate_ip(s):
	    a = s.split('.')
	    if len(a) != 4:
	        return False
	    for x in a:
	        if not x.isdigit():
	            return False
	        i = int(x)
	        if i < 0 or i > 255:
	            return False
	    return True

    @staticmethod
    def haslocalaccess(request):
		if g.islocalbox:
			return False
		
		user_public_ip = request.remote_addr
		user_host = request.host
				
		ping = PingModel.lastping()
		if ping and len(ping) > 0 and user_public_ip == ping["public_ip"]:
			return True
		else:
			return False
			         
    @staticmethod
    def islocal():
    	config = DBHelper.loadconfig()
    	
    	if config["LOCAL"] and config["LOCAL"] == "true":
    		return True
    	else:
    		if config["LOCAL"] and config["LOCAL"] == "false":
				return False
			
    @staticmethod
    def dbinstall():
		DeviceModel.install()

		try:
			PingModel.install()
		except:
		    print "table already exists"
		
		try:
			BoxModel.install()
		except:
		    print "table already exists"
		
		BoxModel.init()		
		FileModel.install()
		FilterHelper.install() 
