import os
from model.file import FileModel
from helper.db import DBHelper
from helper.install import InstallHelper
from PIL import Image

class ImageHelper(object):
    """Helper class for image retrieval and manipulation"""

    _instance = None
    _thumbnail_table = 'file_thumbnail'

    def __new__(cls, base_dir='', theme='', *args, **kwargs):
        """Override __new__ to implement singleton pattern"""

        if not cls._instance:
            cls._instance = super(ImageHelper, cls
                                    ).__new__(cls, *args, **kwargs)
            cls._instance._base_dir = base_dir
            cls._instance._theme = theme
            cls._instance._init()
        return cls._instance

    def _init(self):
        """"""

        self._icons = {}
        icons_dir = os.path.join(self._base_dir, 'icons', self._theme)
        if not os.path.isdir(icons_dir):
            return

        for abspath, dirs, files in os.walk(icons_dir):
            for icon in files:
                size = os.path.basename(abspath)
                if size not in self._icons:
                    self._icons[size] = []
                self._icons[size].append(icon)

    def add_file_icons(self, fileset, small_size, large_size):
        """"""

        sizes = {'icon_small': str(small_size), 'icon_large': str(large_size)}
        for size_key in sizes.keys():
            size = sizes[size_key]
            if size not in self._icons:
                continue

            base_url = 'icons/%s/%s' % (self._theme, size)
            unknown = (
                'unknown.png'
                    if 'unknown.png' in self._icons[size] else None)

            for model in fileset:
                if model.get_data(size_key) is not None:
                    continue
                filename = '%s-%s.png' % (model.type(), model.subtype())
                if filename not in self._icons[size]:
                    filename = unknown
                if filename is not None:
                    model.set_data(size_key, '%s/%s' % (base_url, filename))

    @classmethod
    def join_file_thumbnails(
            cls, select, file_field, width, height, columns=('thumbnail',)):
        """"""

        q = DBHelper.quote_identifier
        width_cond = (('"width" = %d' % width)
                        if width else '"width" IS NULL')
        height_cond = (('"height" = %d' % height)
                        if height else '"height" IS NULL')
        select.left_join(
            (cls._thumbnail_table, 'tt'),
            '%s = tt.file AND %s AND %s' % (
                q(file_field), width_cond, height_cond),
            columns
        )
        return select

    @classmethod
    def add_file_thumbnail(cls, file_id, width, height, thumbnail):
        """"""

        DBHelper().insert(cls._thumbnail_table, {
            'file': file_id,
            'width': width,
            'height': height,
            'thumbnail': thumbnail
        }, True)

    @staticmethod
    def resize(image, width=None, height=None):
        """"""

        if not image:
            return image

        if not width and not height:
            return image

        tosize = [width, height]
        fromsize = image.size
        fromratio = float(fromsize[0]) / fromsize[1]

        if not tosize[0]:
            tosize[0] = tosize[1]*fromratio
        elif not tosize[1]:
            tosize[1] = tosize[0]/fromratio

        toratio = float(tosize[0])/tosize[1]
        tmpsize = ((tosize[0], int(tosize[0]/fromratio))
                        if fromratio < toratio else
                            (int(tosize[1]*fromratio), tosize[1]))

        image = image.resize(tmpsize, Image.ANTIALIAS) #Image.NEAREST

        hcrop = abs(tmpsize[0] - tosize[0])/2
        vcrop = abs(tmpsize[1] - tosize[1])/2
        image = image.crop((
            hcrop,
            vcrop,
            tmpsize[0] - hcrop,
            tmpsize[1] - vcrop
        ))

        return image

    @staticmethod
    def install():
        """Install dependencies and tables"""

        FileModel.install()
        q = DBHelper.quote_identifier
        thumb_table = q(ImageHelper._thumbnail_table)
        file_table = q(FileModel._table)
        file_table_pk = q(FileModel._pk)
        InstallHelper.install('image', (
            lambda: (
                DBHelper().query("""
                    CREATE TABLE %s (
                        "_id"       INTEGER PRIMARY KEY AUTOINCREMENT,
                        "file"      INTEGER NOT NULL DEFAULT 0,
                        "width"     INTEGER,
                        "height"    INTEGER,
                        "thumbnail" TEXT,
                        FOREIGN KEY ("file") REFERENCES %s(%s)
                            ON DELETE CASCADE ON UPDATE CASCADE
                    )
                """ % (thumb_table, file_table, file_table_pk)),
                DBHelper().query("""
                    CREATE UNIQUE INDEX "UNQ_FILE_THUMB_SIZE"
                        ON %s("file", "width", "height")
                """ % thumb_table),
                DBHelper().query("""
                    CREATE INDEX "IDX_FILE_THUMB_WIDTH" ON %s("width")
                """ % thumb_table),
                DBHelper().query("""
                    CREATE INDEX "IDX_FILE_THUMB_HEIGHT" ON %s("height")
                """ % thumb_table)
            ),
        ))

