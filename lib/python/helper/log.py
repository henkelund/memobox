import sys
from model.log import LogModel
from datetime import datetime
from calendar import timegm
from helper.db import DBHelper

class LogHelper(object):
    """Helper class logging"""

    _level = LogModel.DEBUG
    _model_installed = False

    @staticmethod
    def set_level(level):
        """Set logging treshold level"""
        LogHelper._level = level

    @staticmethod
    def get_level():
        """Get logging treshold level"""
        return LogHelper._level

    @staticmethod
    def log(message, level):
        """Log a message at a given level
        Returns the created log entry, if any
        """

        if level > LogHelper._level:
            return None

        if not LogHelper._model_installed:
            LogModel.install()
            LogHelper._model_installed = True

        return LogModel({
            'message': message,
            'level': level,
            'created_at': timegm(datetime.utcnow().utctimetuple())
        }).save()

    @staticmethod
    def emerg(message):
        """Log an emergency message"""
        return LogHelper.log(message, LogModel.EMERG)

    @staticmethod
    def alert(message):
        """Log an alert message"""
        return LogHelper.log(message, LogModel.ALERT)

    @staticmethod
    def crit(message):
        """Log a critical message"""
        return LogHelper.log(message, LogModel.CRIT)

    @staticmethod
    def error(message):
        """Log an error message"""
        return LogHelper.log(message, LogModel.ERROR)

    @staticmethod
    def warn(message):
        """Log a warning message"""
        return LogHelper.log(message, LogModel.WARN)

    @staticmethod
    def notice(message):
        """Log a notice message"""
        return LogHelper.log(message, LogModel.NOTICE)

    @staticmethod
    def info(message):
        """Log an info message"""
        return LogHelper.log(message, LogModel.INFO)

    @staticmethod
    def debug(message):
        """Log a debug message"""
        return LogHelper.log(message, LogModel.DEBUG)

if (__name__ == '__main__'):
    """$ python log.py path/to/database message level"""

    if len(sys.argv) < 3:
        exit(1)

    try:
        DBHelper(sys.argv[1])
    except:
        exit(2)

    message = sys.argv[2]
    if len(message) == 0:
        exit(3)

    level = None
    if len(sys.argv) >= 4:
        level_str = sys.argv[3][:2].lower()
        if level_str == 'em':
            level = LogModel.EMERG
        elif level_str == 'al':
            level = LogModel.ALERT
        elif level_str == 'cr':
            level = LogModel.CRIT
        elif level_str == 'er':
            level = LogModel.ERROR
        elif level_str == 'wa':
            level = LogModel.WARN
        elif level_str == 'no':
            level = LogModel.NOTICE
        elif level_str == 'in':
            level = LogModel.INFO

    if level is None:
        level = LogModel.DEBUG

    try:
        LogHelper.log(message, level)
    except:
        exit(4)

    exit(0)

