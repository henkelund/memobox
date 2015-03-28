from helper.db import DBHelper, DBSelect
from inspect import isroutine
from model.config import ConfigModel
from flask import Flask, session, g
import urllib2, json

class EventHelper(object):
    """Helper class for user access management"""

    EVENT_TYPES = [
    	"SYSTEM",
   		"INFORMATION", 
   		"CONFIGURATION", 
   		"REBOOT", 
   		"SHUTDOWN"
    ]

    @staticmethod
    def parse_events(data):
        response = urllib2.urlopen(data)
        html = response.read()
        j = json.loads(html)

        if 'messages' in j:
            for message in j["messages"]:
            	if EventHelper.EVENT_TYPES[int(message["type"])] == EventHelper.EVENT_TYPES[2]:
                    key = message["message"].split("=")[0]
                    value = message["message"].split("=")[1]

                    try:
                        c = ConfigModel.get_param(key)
                        c.set_param("key", key)
                        c.set_param("value", value)
                        c.save()
                    except IndexError as e:
                        print e

        return j
