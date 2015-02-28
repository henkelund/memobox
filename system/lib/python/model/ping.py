import subprocess
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
         find = subprocess.Popen(['find', '/backups/'+config["BOXUSER"]+'/cache', '-type', 'f'],stdout=subprocess.PIPE)
         wc = subprocess.Popen(['wc', '-l'], stdin = find.stdout, stdout=subprocess.PIPE)
         remote_cachecount = wc.stdout.readline().replace("\\n", "")

         # Count files in cache folder
         find = subprocess.Popen(['find', '/backups/'+config["BOXUSER"]+'/devices', '-type', 'f'],stdout=subprocess.PIPE)
         wc = subprocess.Popen(['wc', '-l'], stdin = find.stdout, stdout=subprocess.PIPE)
         remote_devicecount = wc.stdout.readline().replace("\\n", "")

         print "removedev:"+remote_devicecount
         print "removecache:"+remote_cachecount
         
         pings = DBSelect('ping','count(*) as pingcount').where("uuid = '%s'" % uuid).query()
         pingcount = 0; 

         for ping in pings:
         	pingcount = ping['pingcount']
         
         if pingcount == 0:
	         DBHelper().query(
	                    """
	                        INSERT INTO ping (local_ip, public_ip, uuid, capacity, used_space, last_ping, username, devicecount, cachecount, remote_devicecount, remote_cachecount, temp, software) VALUES("%s", "%s", "%s", "%s", "%s", datetime(), "%s", "%s", "%s", "%s", "%s", "%s", "%s")
	                    """ % (local_ip, public_ip, uuid, capacity, used_space, username, devicecount, cachecount, remote_devicecount, remote_cachecount, temp))
         else:
	         print "Temp: "+str(temp)
	         DBHelper().query(
	                    """
	                        UPDATE ping SET local_ip = "%s", public_ip = "%s", capacity = "%s", used_space = "%s", last_ping = datetime(), username = "%s", devicecount = "%s", cachecount = "%s", remote_devicecount = "%s", remote_cachecount = "%s", temp = "%s", software = "%s" WHERE uuid = "%s"
	                    """ % (local_ip, public_ip, capacity, used_space, username, devicecount, cachecount, remote_devicecount, remote_cachecount, temp, software, uuid))

    @staticmethod
    def lastping():
         _ping = {}
         
         _sqlite = subprocess.Popen(['sqlite3', '/backups/'+g.username+'/ping.db', 'SELECT * FROM ping WHERE LENGTH(uuid) > 10 ORDER BY last_ping DESC LIMIT 1'], stdout=subprocess.PIPE)
         _db_ping = _sqlite.stdout.readline()
         
         if not _db_ping or len(_db_ping) == 0:
         	return None
         else:
	         _ping_array = _db_ping.split("|")
	         
	         if len(_ping_array) < 12:
	         	return None
	         	
	         else:
	         	_ping["local_ip"] = _ping_array[1]
	         	_ping["public_ip"] = _ping_array[2]
	         	_ping["uuid"] = _ping_array[3]
	         	_ping["capacity"] = _ping_array[4]
	         	_ping["used_space"] = _ping_array[5]
	         	_ping["last_ping"] = _ping_array[6]
	         	_ping["username"] = _ping_array[7]
	         	_ping["devicecount"] = _ping_array[8]
	         	_ping["cachecount"] = _ping_array[9]
	         	_ping["remote_devicecount"] = _ping_array[10].rstrip()
	         	_ping["remote_cachecount"] = _ping_array[11].rstrip()
	         
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
