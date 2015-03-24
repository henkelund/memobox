from base import BaseModel
from helper.db import DBHelper
from helper.db import DBSelect
from datetime import date
from datetime import datetime
from glob import glob
import os
import json
import collections
import MySQLdb as mdb

class MessageModel(BaseModel):
    """Model for messages between box and cloud server"""

    def __init__(self, message_id, box, status, type, message):
        self.id         = message_id
        self.box        = box
        self.status     = status
        self.type       = type
        self.message    = message

    def values(self):
        values = {
            "id": self.id,
            "status": self.status,
            "type": self.type,
            "message": self.message,
        }
        
        return values

    def send(self):
        con = None

        try:
            con = mdb.connect('localhost', 'root', 'root', 'backupbox');
            cur = con.cursor()
            cur.execute("INSERT INTO messages (box, status, type,  message) VALUES("+str(self.box)+", 0, "+str(self.type)+" , '"+self.message+"')")
            con.commit()

        except mdb.Error, e:
            print "Error %d: %s" % (e.args[0],e.args[1])

        finally:    
            if con:    
                con.close()


    def mark_as_read(self):
        con = None

        try:
            con = mdb.connect('localhost', 'root', 'root', 'backupbox');
            cur = con.cursor()
            cur.execute("UPDATE messages SET status = 1 WHERE box = " + str(self.box))
            con.commit()

        except mdb.Error, e:
            print "Error %d: %s" % (e.args[0],e.args[1])

        finally:    
            if con:    
                con.close()

    @staticmethod
    def get_box_by_uuid(uuid):
        con = None
        box_id = -1

        try:
            con = mdb.connect('localhost', 'root', 'root', 'backupbox');
            cur = con.cursor()
            cur.execute("SELECT id FROM ping WHERE uuid = '"+uuid+"'")
            rows = cur.fetchall()

            for row in rows:
                box_id = row[0]

        except mdb.Error, e:
            print "Error %d: %s" % (e.args[0],e.args[1])

        finally:    
            if con:    
                con.close()

        return box_id

    @staticmethod
    def load_messages(uuid):
        _messages = []
        con = None

        try:
            con = mdb.connect('localhost', 'root', 'root', 'backupbox');
            cur = con.cursor()
            cur.execute("SELECT * FROM messages JOIN ping ON messages.box = ping.id WHERE status = 0 AND uuid = '" + uuid + "'")
            rows = cur.fetchall()

            for row in rows:
                m = MessageModel(row[0], row[1], row[2], row[3], row[4])
                _messages.append(m)

        except mdb.Error, e:
            print "Error %d: %s" % (e.args[0],e.args[1])

        finally:    
            if con:    
                con.close()

        return _messages