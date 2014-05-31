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

