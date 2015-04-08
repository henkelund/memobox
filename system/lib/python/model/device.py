from base import BaseModel
from helper.db import DBHelper
from helper.db import DBSelect
from datetime import date
from datetime import datetime
import os, urllib2, collections
from glob import glob

class DeviceModel(BaseModel):
    """Model describing a USB device"""

    _table = 'device'
    _pk = '_id'
    _daterange = {}
    _typecount = {}

    READY                       = 0
    MOUNTING                    = 1
    BACKUP_STARTED              = 2
    BACKUP_INTERRUPTED          = 3
    BACKUP_COMPLETE             = 4
    FILE_INDEX_STARTED          = 5
    FILE_INDEX_COMPLETE         = 6
    THUMBNAIL_INDEX_STARTED     = 7

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

    def set_state(self, state):
        self.set_data('state', state)
        self.save()

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

    def get_typecount(self, device):
        #SELECT device, file.type, count(*) as count FROM "file" INNER JOIN "device" ON device._id = file.device GROUP BY device,file.type;
        if len(self._typecount) == 0:
            typecount = DBSelect('file',"device, file.type as t, count(*) as count").where("is_hidden = 0").join("device", "device._id = file.device").group("device").group("t")
            result = typecount.query();
            
            _lastdevice = -1
            _data = {}
            _total = 0

            for r in result:
                if int(r["device"]) != _lastdevice:
                    if _lastdevice != -1:
                        _data["all"] = _total
                        self._typecount[_lastdevice] = _data
                    _data = {}
                    _total = 0
                    _lastdevice = int(r["device"])

                _data[r["t"]]   = int(r["count"])
                _total = _total + int(r["count"])

            _data["all"] = _total
            self._typecount[_lastdevice] = _data

            _images = 0
            _videos = 0
            _documents = 0
            
            for key, value in self._typecount.iteritems():
                if "image" in value:
                    _images += int(value["image"])

                if "video" in value:
                    _videos += int(value["video"])

                _documents += int(value["all"])

            self._typecount[-1] = { "images": _images, "videos": _videos, "documents": (_documents - _images - _videos) }

        if device in self._typecount:
            return self._typecount[device]
        else:
            return {}

    def get_daterange(self, device):
        if len(self._daterange) == 0:
            date_range = DBSelect('file',"device, strftime('%Y-%m', datetime(created_at, 'unixepoch')) as date, count(strftime('%Y-%m', datetime(created_at, 'unixepoch'))) as files").where("is_hidden = 0").where("width = 260").join("file_thumbnail", "file._id = file_thumbnail.file").group("device").group("date").order('device','DESC').order('date', 'DESC')
            rang = date_range.query()
            
            _lastdevice = -1
            _data = []

            for r in rang:
                if int(r["device"]) != _lastdevice:
                    if _lastdevice != -1:
                        self._daterange[_lastdevice] = _data
                    _data = []
                    _lastdevice = int(r["device"])

                _temp = {}
                _temp["date"]   = r["date"]
                _temp["files"]  = r["files"]
                _data.append(_temp)

            self._daterange[int(_lastdevice)] = _data

            _all = {}
            _all_months = []

            for key, value in self._daterange.iteritems():
                for month in value:
                    if month["date"] in _all:
                        _all[month["date"]] += month["files"]
                    else:
                        _all[month["date"]] = month["files"]
            
            _all = collections.OrderedDict(sorted(_all.items(), reverse=True))

            for key, value in _all.iteritems():
                _all_months.append({ "date": key, "files":value });

            self._daterange[-1] = _all_months

        if int(device) in self._daterange:
            return self._daterange[int(device)]
        else:
            return {}

    def get_backups(self):
        tree = {}
        #os.chdir(self._basedir)
        #for node in os.listdir(self._basedir):
        res = []
        path = "../data/devices/"+str(self.serial())+"/backups"
        for root,dirs,files in os.walk(path, topdown=True):
            depth = root[len(path) + len(os.path.sep):].count(os.path.sep)
            if depth == 1:
                # We're currently two directories in, so all subdirs have depth 3
                res += [os.path.join(root.replace(path+"/", ""), d) for d in dirs]
                dirs[:] = [] # Don't recurse any deeper

        #tree[node] = res

        _dates = []

        #for key in tree:
        #    _dates[key] = []
        #    for value in tree[key]:
        #        _d = value.split("/")
        #        mydate = date(int(_d[0]),int(_d[1]) , int(_d[2]))  #year, month, day
        #        _dates[key].append(mydate)
        #    _dates[key].sort()

        for value in res:
            _d = value.split("/")
            mydate = str(date(int(_d[0]),int(_d[1]) , int(_d[2])))  #year, month, day
            _dates.append(mydate)
        _dates.sort()


        return _dates

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

