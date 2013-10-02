import sys
from datetime import datetime
from helper.db import DBHelper, DBSelect
from helper.install import InstallHelper
from helper.filter import FilterHelper
from model.file import FileModel

class FileTimeIndexer(object):
    """Class responsible for indexing file times"""

    @staticmethod
    def install():
        """Install dependencies"""

        FileModel.install()
        FilterHelper.install()

    @classmethod
    def get_time_attribute(cls):
        """Return the exif DateTime corresponding attribute"""

        if not hasattr(cls, '_time_attr'):
            for attr in FileModel.get_all_attributes():
                if attr['code'] == 'timestamp':
                    cls._time_attr = attr
                    break

        return cls._time_attr

    @staticmethod
    def get_time_attr_select():
        """Return a DBSelect object with file timestamp values"""

        attr = FileTimeIndexer.get_time_attribute()
        table = '%s_attribute_%s' % (attr['parent'], attr['type'])

        return DBSelect((table, 'tt')
                    ).where('tt.attribute = ?', attr['_id']
                    ).where('tt.value IS NOT NULL'
                    ).where('tt.value > 0')

    @staticmethod
    def index_seasons():
        """Figure out season for files with timestamps"""

        FileTimeIndexer.install()

        filter_code = 'season'
        FilterHelper.create_filter(filter_code, 'Season')
        FilterHelper.add_filter_option(filter_code, 0, 'Spring')
        FilterHelper.add_filter_option(filter_code, 1, 'Summer')
        FilterHelper.add_filter_option(filter_code, 2, 'Fall')
        FilterHelper.add_filter_option(filter_code, 3, 'Winter')

        time_select = FileTimeIndexer.get_time_attr_select()

        # join on value table to find not yet indexed files
        FilterHelper.join_filter_values(time_select, filter_code, 'tt.parent')
        time_select.where('fv.file IS NULL').limit(100)

        for time in time_select.query().fetchall():
            try:
                month = int(datetime.fromtimestamp(time['value']).strftime('%m'))
                shifted = (month - 3)%12 # makes march = 0, first month of spring
                FilterHelper.set_filter_values(
                    time['parent'], filter_code, shifted/3)
            except ValueError:
                pass # invalid format

    @staticmethod
    def index_time_of_day():
        """Figure out time of day for files with timestamps"""

        FileTimeIndexer.install()

        filter_code = 'tod' # time-of-day
        FilterHelper.create_filter(filter_code, 'Time of Day')
        FilterHelper.add_filter_option(filter_code, 0, 'Morning')
        FilterHelper.add_filter_option(filter_code, 1, 'Noon')
        FilterHelper.add_filter_option(filter_code, 2, 'Afternoon')
        FilterHelper.add_filter_option(filter_code, 3, 'Evening')
        FilterHelper.add_filter_option(filter_code, 4, 'Night')

        time_select = FileTimeIndexer.get_time_attr_select()

        # join on value table to find not yet indexed files
        FilterHelper.join_filter_values(time_select, filter_code, 'tt.parent')
        time_select.where('fv.file IS NULL').limit(100)

        for time in time_select.query().fetchall():
            try:
                hour = int(datetime.fromtimestamp(time['value']).strftime('%H'))
                tod = 4 # Night
                if hour >= 5 and hour <= 10:
                    tod = 0 # Morning
                elif hour >= 11 and hour <= 13:
                    tod = 1 # Noon
                elif hour >= 14 and hour <= 17:
                    tod = 2 # Afternoon
                elif hour >= 18 and hour <= 21:
                    tod = 3 # Evening

                FilterHelper.set_filter_values(
                    time['parent'], filter_code, tod)
            except ValueError:
                pass # invalid format

if (__name__ == '__main__'):
    """$ python filetime.py path/to/database"""

    if len(sys.argv) < 2:
        exit(1)

    database = sys.argv[1]

    DBHelper(database)
    FileTimeIndexer.index_seasons()
    FileTimeIndexer.index_time_of_day()

