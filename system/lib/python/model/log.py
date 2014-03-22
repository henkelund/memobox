from base import BaseModel
from helper.db import DBHelper

class LogModel(BaseModel):
    """Model describing a database log entry"""

    EMERG = 0
    ALERT = 1
    CRIT = 2
    ERROR = 3
    WARN = 4
    NOTICE = 5
    INFO = 6
    DEBUG = 7

    _table = 'log'
    _pk = '_id'

    @classmethod
    def _install(cls):
        """Define install routines for this model"""

        table = DBHelper.quote_identifier(cls._table)
        pk = DBHelper.quote_identifier(cls._pk)
        return (
            lambda: (
                DBHelper().query("""
                    CREATE TABLE %s (
                        %s           INTEGER PRIMARY KEY AUTOINCREMENT,
                        "level"      INTEGER NOT NULL DEFAULT %d,
                        "message"    TEXT NOT NULL DEFAULT '',
                        "created_at" INTEGER NOT NULL DEFAULT (STRFTIME('%%s', 'now'))
                    )""" % (table, pk, cls.DEBUG)),
                DBHelper().query(
                    'CREATE INDEX "IDX_LOG_LEVEL" ON %s ("level")'
                        % table),
                DBHelper().query(
                    'CREATE INDEX "IDX_LOG_CREATED_AT" ON %s ("created_at")'
                        % table)
            ),
        )

