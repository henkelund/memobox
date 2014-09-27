from base import BaseModel
from helper.db import DBHelper
import os
from glob import glob

class DeviceModel(BaseModel):
    """Model describing a USB device"""

    _table = 'device'
    _pk = '_id'
    _info_file_map = {
        'serial': 'serial',
        'product_id': 'idProduct',
        'product_name': 'product',
        'model': 'model',
        'vendor_id': 'idVendor',
        'vendor_name': 'vendor',
        'manufacturer': 'manufacturer',
        'last_backup': 'last_backup',
        'state': 'state',
        'new': 'new',
        'password': 'password'
    }

    def get_transfer_dirs(self):
        """Return this devices transfer directories"""

        base_dir = self.directory() + '/' if self.directory() else ''
        trans_dirs = glob('%sbackups/????/??/??/??????' % base_dir)
        return [d for d in trans_dirs if os.path.isdir(d)]

    def load_by_dir(self, directory):
        """Load a this model given its base directory"""

        if not os.path.isdir(directory):
            return self

        serial_file = os.path.join(directory, 'serial')
        if not os.path.isfile(serial_file):
            return self

        self.directory(directory)
        fh = open(serial_file, 'r')
        serial = fh.readline().strip()
        fh.close()

        self.load(serial, 'serial')
        if self.id():
            # new info is not saved if serial already exists
            return self

        for field in self._info_file_map:
            filepath = os.path.join(directory, self._info_file_map[field])
            if not os.path.isfile(filepath):
                continue
            fh = open(filepath, 'r')
            self.set_data(field, fh.readline().strip())
            fh.close()

        self.save()
        return self

    def image_count(self, device_id):
	    counts = DBHelper().query("SELECT COUNT(*) as image_count FROM file WHERE device = %s AND type = 'image'" % device_id);
	    for count in counts:
	    	return count['image_count']

    def video_count(self, device_id):
	    counts = DBHelper().query("SELECT COUNT(*) as video_count FROM file WHERE device = %s AND type = 'video'" % device_id);
	    for count in counts:
	    	return count['video_count']

    def last_backup(self, device_id):
	    backups = DBHelper().query("SELECT indexed_at as last_backup FROM file WHERE device = %s ORDER BY indexed_at DESC LIMIT 1;" % device_id);
	    for backup in backups:
	    	return backup['last_backup']

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
                            "product_id"   TEXT NOT NULL DEFAULT '',
                            "product_name" TEXT NOT NULL DEFAULT '',
                            "model"        TEXT NOT NULL DEFAULT '',
                            "vendor_id"    TEXT NOT NULL DEFAULT '',
                            "vendor_name"  TEXT NOT NULL DEFAULT '',
                            "manufacturer" TEXT NOT NULL DEFAULT '',
                            "password"     TEXT DEFAULT NULL,
                            "last_backup" DATETIME,
                            "state" INT NOT NULL DEFAULT 3, 
                            "type" INT NOT NULL DEFAULT 1,
                            "new" INT NOT NULL DEFAULT 1,
                            "locked" INT NOT NULL DEFAULT 0
                        )
                    """ % table),
                DBHelper().query(
                    'CREATE UNIQUE INDEX "UNQ_DEVICE_SERIAL" ON %s ("serial")'
                         % table)
            ),
        )

