from helper.db import DBHelper, DBSelect
from inspect import isroutine
from model.ping import PingModel
from flask import Flask, session, g

class AccessHelper(object):
    """Helper class for user access management"""

    @staticmethod
    def authorized(username):
		if(g.islocal == False and (("verified_"+username not in session) or (session["verified_"+username] == False))):
			return False
		else:
			return True
	
    @staticmethod
    def requestuser(base_url):
    	return base_url.split(".")[0].split("//")[1]