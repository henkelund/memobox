from helper.db import DBHelper, DBSelect
from inspect import isroutine
from model.config import ConfigModel
from flask import Flask, session, g
import urllib2, json, subprocess

class EventHelper(object):
    """Helper class for user access management"""

    EVENT_SYSTEM        = 0 # Not used at the moment
    EVENT_INFORMATION   = 1 # Not used at the moment
    EVENT_CONFIGURATION = 2
    EVENT_REBOOT        = 3
    EVENT_SHUTDOWN      = 4 # Not used at the moment
    EVENT_UPDATE        = 5
    EVENT_LOGBACKUP     = 6
    EVENT_FULLBACKUP    = 7 # Not used at the moment

    @staticmethod
    def parse_events(data):
        response = urllib2.urlopen(data)
        html = response.read()
        j = json.loads(html)

        if 'messages' in j:
            for message in j["messages"]:
                message_id = int(message["type"])
            	if message_id == EventHelper.EVENT_CONFIGURATION:
                    key = message["message"].split("=")[0]
                    value = message["message"].split("=")[1]

                    try:
                        c = ConfigModel.get_param(key)
                        c.set_param("key", key)
                        c.set_param("value", value)
                        c.save()
                    except IndexError as e:
                        print e
                elif message_id == EventHelper.EVENT_REBOOT:
                    subprocess.call(['/sbin/reboot'])
                elif message_id == EventHelper.EVENT_UPDATE:
                    subprocess.call(['/backupbox/system/bin/update.sh'])
                elif message_id == EventHelper.EVENT_LOGBACKUP:
                    subprocess.call(['/backupbox/system/bin/backup.sh', 'LOGBACKUP'])

        return j

