# -*- coding: utf-8 -*-
import sys, os, json
import subprocess
from helper.db import DBHelper, DBSelect
from helper.image import ImageHelper
from model.file import FileModel
from helper.log import LogHelper as logger
from model.device import DeviceModel
from helper.event import EventHelper
from model.config import ConfigModel


if (__name__ == '__main__'):
    """$ python image.py path/to/database path/to/basedir"""
	
    DBHelper.initdb("/backupbox/data/index.db", True)
    json = EventHelper.parse_events(sys.argv[1])
    if 'status' in json:
    	print json["status"] 