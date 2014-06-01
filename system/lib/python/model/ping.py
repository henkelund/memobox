import subprocess
from base import BaseModel
from helper.db import DBHelper, DBSelect
import os
from glob import glob

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
                        "last_ping"	   DATETIME
                    )
                """)
        )
    @staticmethod
    def ping(local_ip, public_ip, uuid, capacity, used_space):
         pings = DBSelect('ping','count(*) as pingcount').where("uuid = '%s'" % uuid).query()
         pingcount = 0; 

         for ping in pings:
         	pingcount = ping['pingcount']
         
         if pingcount == 0:
	         DBHelper().query(
	                    """
	                        INSERT INTO ping (local_ip, public_ip, uuid, capacity, used_space, last_ping) VALUES("%s", "%s", "%s", "%s", "%s", datetime())
	                    """ % (local_ip, public_ip, uuid, capacity, used_space))
         else:
	         DBHelper().query(
	                    """
	                        UPDATE ping SET local_ip = "%s", public_ip = "%s", capacity = "%s", used_space = "%s", last_ping = datetime() WHERE uuid = "%s"
	                    """ % (local_ip, public_ip, capacity, used_space, uuid))

    @staticmethod
    def lastping():
         _ping = {}
         pings = DBSelect('ping','*').where("uuid not null AND uuid is not 'None' AND uuid is not ''").query()
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
