from helper.db import DBHelper, DBSelect
from inspect import isroutine
from model.ping import PingModel
from flask import Flask, session

class AccessHelper(object):
    """Helper class for user access management"""

    @staticmethod
    def authorized():
		print "Hello World!"
		if(PingModel.islocal() == False and (("verified" not in session) or (session["verified"] == False))):
			return False
		else:
			return True
	
    @staticmethod
    def requestuser(base_url):
    	return base_url.split(".")[0].split("//")[1]