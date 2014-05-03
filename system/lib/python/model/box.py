import subprocess
from base import BaseModel
from helper.db import DBHelper, DBSelect
import os
from glob import glob

class BoxModel(BaseModel):
    """Model describing a box system info"""

    _table = 'box'
    _pk = '_id'
    _info_file_map = {
        'serial': 'serial',
        'username': 'username'
    }

    @classmethod
    def _install(cls):
        """Define install routines for this model"""

        table = DBHelper.quote_identifier(cls._table)
        return (
            lambda: (
                DBHelper().query(
                    """
                        CREATE TABLE %s (
                            "_id"          INTEGER PRIMARY KEY AUTOINCREMENT,
                            "serial"       TEXT NOT NULL DEFAULT '',
                            "username"   TEXT NOT NULL DEFAULT ''
                        )
                    """ % table),
                DBHelper().query(
                    'CREATE UNIQUE INDEX "UNQ_DEVICE_SERIAL" ON %s ("serial")'
                         % table)
            ),
        )
    @classmethod
    def init(cls):
         cmdline = [
         'blkid',
         '-s',
         'UUID',
         '-o',
         'value',
         '/dev/sda1'
         ]   		
        		
       	 # Get serial of Hard drive and store id to database
         blkid = subprocess.Popen(cmdline,stdout=subprocess.PIPE)
         serial = blkid.stdout.readline()
         print serial
                  
         table = DBHelper.quote_identifier(cls._table)
         
         boxes = DBSelect('box','count(*) as boxcount').where("serial = '%s'" % serial).query()
         boxcount = 0; 

         for box in boxes:
         	boxcount = box['boxcount']
         
         if boxcount == 0:
	         DBHelper().query(
	                    """
	                        INSERT INTO %s (serial) VALUES("%s")
	                    """ % (table, serial))

