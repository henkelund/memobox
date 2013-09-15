import sys, os, re, sqlite3
from helper.db import DBHelper
from model.device import DeviceModel
from model.file import FileModel
from datetime import datetime

class FileIndexer(object):
    """"""

    def __init__(self, basedir):
        """"""
        self._basedir = basedir

    def index_all_devices(self):
        """"""

        os.chdir(self._basedir)
        for node in os.listdir(self._basedir):
            device = DeviceModel().load_by_dir(node)
            if device.id() is not None:
                self.index_device(device)

    def index_device(self, device):
        """"""

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
                        #TODO: unlink file if duplicate found?
                        print '[%s] %s already exists, skipping..' % (
                                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                    os.path.join(devpath, filename))

            open(flagfile, 'w').close()

if (__name__ == '__main__'):
    """"""

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

