import subprocess
from base import BaseModel
from helper.db import DBHelper, DBSelect
from helper.filter import FilterHelper
from model.device import DeviceModel
from model.box import BoxModel
from model.file import FileModel


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
                        "username"     TEXT NOT NULL DEFAULT ''
                    )
                """)
        )
    @staticmethod
    def ping(local_ip, public_ip, uuid, capacity, used_space, username):
         config = PingModel.loadconfig()
         pings = DBSelect('ping','count(*) as pingcount').where("uuid = '%s'" % uuid).query()
         pingcount = 0; 

         for ping in pings:
         	pingcount = ping['pingcount']
         
         if pingcount == 0:
	         DBHelper().query(
	                    """
	                        INSERT INTO ping (local_ip, public_ip, uuid, capacity, used_space, last_ping, username) VALUES("%s", "%s", "%s", "%s", "%s", datetime(), "%s")
	                    """ % (local_ip, public_ip, uuid, capacity, used_space, username))
         else:
	         DBHelper().query(
	                    """
	                        UPDATE ping SET local_ip = "%s", public_ip = "%s", capacity = "%s", used_space = "%s", last_ping = datetime(), username = "%s" WHERE uuid = "%s"
	                    """ % (local_ip, public_ip, capacity, used_space, username, uuid))

    @staticmethod
    def lastping():
         _ping = {}
         pings = DBSelect('ping','*').where("uuid not null AND uuid is not 'None' AND uuid is not '' AND uuid is not 'null'").query()
         pingcount = 0; 

         for ping in pings:
         	_ping["local_ip"] = ping["local_ip"];
         	_ping["public_ip"] = ping["public_ip"];
         	_ping["last_ping"] = ping["last_ping"];
         	_ping["capacity"] = ping["capacity"];
         	_ping["used_space"] = ping["used_space"];
         	_ping["uuid"] = ping["uuid"];
         
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
		ping = PingModel.lastping()
		ping["user_public_ip"] = request.remote_addr
		ping["user_host"] = request.host
		
		if PingModel.validate_ip(ping["user_host"]):
			return False
		else:
			if ping["user_public_ip"] == ping["public_ip"]:
				return True
			else:
				return False
			         
    @staticmethod
    def islocal():
    	config = PingModel.loadconfig()
    	
    	if config["LOCAL"] and config["LOCAL"] == "true":
    		return True
    	else:
    		if config["LOCAL"] and config["LOCAL"] == "false":
				return False

    @staticmethod
    def initdb(remote_addr, base_url):
    	config = PingModel.loadconfig()
    	
    	if config["LOCAL"] and config["LOCAL"] == "true":
			DBHelper("../data/index.db")
    	else:
    		if config["BOXUSER"] and config["BOXUSER"] != "null":
				DBHelper("/backups/"+config["BOXUSER"]+"/index.db")
    		else:
				DBHelper("/backups/"+base_url.split(".")[0].split("//")[1]+"/index.db")
			
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

    @staticmethod
    def loadconfig(username=None):
		config = {}
		
		if username is not None:
			with open("/backups/"+username+"/local.cfg") as f:
				content = f.readlines()
		else:
			with open("../data/local.cfg") as f:
				content = f.readlines()
		
		for line in content:
			if len(line.split("=")) == 2:
				config[line.split("=")[0]] = line.split("=")[1].replace('"', '').replace('\n', '')
		
		return config
