from base import BaseModel
from helper.db import DBHelper
from helper.db import DBSelect
from datetime import date
from datetime import datetime
import os
import urllib2
import json
import collections
from glob import glob

class ConfigModel(BaseModel):
    """User Configuration"""

    _table = 'config'
    _pk = '_id'

    def set_param(self, key, value):
        self.set_data(key, value)

    @staticmethod
    def get_param(key):
        _config = ConfigModel()
        models = ConfigModel.all().where("key = '"+key+"'")
        
        for model in models: 
            _config = model

        return _config

    @staticmethod
    def get_all_params():
        _params = []
        models = ConfigModel.all().query()

        for model in models: 
            _params.append(model)

        return _params

    @classmethod
    def _install(cls):
        """Define install routines for this model"""
        table = DBHelper.quote_identifier(cls._table)
        return (
            lambda: (
                DBHelper().query(
                    """
                        CREATE TABLE %s (
                            "_id"           INTEGER PRIMARY KEY AUTOINCREMENT,
                            "key"           TEXT NOT NULL UNIQUE DEFAULT '',
                            "value"         TEXT NOT NULL DEFAULT '',
                            "created_at"    DATETIME DEFAULT CURRENT_TIMESTAMP,
                            "modified_at"   DATETIME DEFAULT CURRENT_TIMESTAMP
                        )
                    """ % table),
                DBHelper().query(
                    'CREATE UNIQUE INDEX "UNQ_CONFIG" ON %s ("%s")'
                         % table, cls._pk)

            ),
        )