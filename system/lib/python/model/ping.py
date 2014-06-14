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
                        "username"     TEXT NOT NULL DEFAULT '', 
                        "devicecount"  INT, 
                        "cachecount"   INT
                    )
                """)
        )
    @staticmethod
    def ping(local_ip, public_ip, uuid, capacity, used_space, username, devicecount, cachecount):
         config = DBHelper.loadconfig()
         pings = DBSelect('ping','count(*) as pingcount').where("uuid = '%s'" % uuid).query()
         pingcount = 0; 

         for ping in pings:
         	pingcount = ping['pingcount']
         
         if pingcount == 0:
	         DBHelper().query(
	                    """
	                        INSERT INTO ping (local_ip, public_ip, uuid, capacity, used_space, last_ping, username, devicecount, cachecount) VALUES("%s", "%s", "%s", "%s", "%s", datetime(), "%s", "%s", "%s")
	                    """ % (local_ip, public_ip, uuid, capacity, used_space, username, devicecount, cachecount))
         else:
	         DBHelper().query(
	                    """
	                        UPDATE ping SET local_ip = "%s", public_ip = "%s", capacity = "%s", used_space = "%s", last_ping = datetime(), username = "%s", devicecount = "%s", cachecount = "%s" WHERE uuid = "%s"
	                    """ % (local_ip, public_ip, capacity, used_space, username, uuid, devicecount, cachecount))

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
         	_ping["devicecount"] = ping["devicecount"];
         	_ping["cachecount"] = ping["cachecount"];
         
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
		user_public_ip = request.remote_addr
		user_host = request.host
		
		if PingModel.validate_ip(user_host):
			return False
		else:
			if len(ping) > 0 and user_public_ip == ping["public_ip"]:
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
