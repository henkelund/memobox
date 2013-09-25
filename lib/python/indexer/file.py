import sys, os, re, sqlite3
from helper.db import DBHelper
from model.device import DeviceModel
from model.file import FileModel
from datetime import datetime

class FileIndexer(object):
    """Class responsible for indexing data from new files"""

    def __init__(self, basedir):
        """Initialize this indexer"""
        self._basedir = basedir

    def index_all_devices(self):
        """Index files for every folder that qualifies as a device within
        the current directory
        """

        os.chdir(self._basedir)
        for node in os.listdir(self._basedir):
            device = DeviceModel().load_by_dir(node)
            if device.id() is not None:
                self.index_device(device)

    def index_device(self, device):
        """Index all new files for a given device"""

        transfer_dirs = device.get_transfer_dirs()
        for transfer_dir in transfer_dirs:

            abstrans = os.path.join(self._basedir, transfer_dir)
            flagfile = os.path.join(abstrans, '.__indexed__')

            if os.path.isfile(flagfile):
                continue

            for abspath, dirs, files in os.walk(abstrans):
                for filename in files:
                    devpath = re.sub(r'^%s' % re.escape(abstrans), '', abspath)
                    absfile = os.path.join(abspath, filename)
                    file_model = FileModel.factory(absfile)
                    file_model.add_data({
                        'devpath': devpath,
                        'device': device.id()
                    })
                    try:
                        file_model.save()
                    except sqlite3.IntegrityError:
                        log_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                        # unique index on "name", "devpath" and "checksum"
                        duplicates = FileModel.all().where(
                            'name = ?', file_model.name()).where(
                            'devpath = ?', file_model.devpath()).where(
                            'checksum = ?', file_model.checksum()).limit(1)

                        if (len(duplicates) > 0
                            and duplicates[0].abspath()
                                != file_model.abspath()):
                            # the new file is identical to an old one but not
                            # the same file, lets unlik it.
                            try:
                                os.unlink(file_model.abspath())
                                print '[%s] Removed duplicate %s' % (
                                                log_time, file_model.abspath())
                            except OSError:
                                print '[%s] Unable to remove duplicate %s' % (
                                                log_time, file_model.abspath())

                        print '[%s] %s already exists, skipping..' % (
                                    log_time,
                                    os.path.join(devpath, filename))

            open(flagfile, 'w').close() # touch indexed flag

if (__name__ == '__main__'):
    """~$ python file.py path/to/basedir path/to/database"""

    if len(sys.argv) < 2:
        exit(1)

    basedir = sys.argv[1]
    database = sys.argv[2]

    if not os.path.isdir(basedir):
        exit(2)

    DBHelper(database)
    DeviceModel.install()
    FileModel.install()
    FileIndexer(basedir).index_all_devices()

