import sys, os
import subprocess
from PIL import Image
from helper.db import DBHelper, DBSelect
from helper.image import ImageHelper
from model.file import FileModel

class ImageIndexer(object):
    """Class responsible for generating thumbnails"""

    @classmethod
    def index_file_thumbnails(cls, basedir, width, height):
        """Generate thumbnails for image files"""

        ImageHelper.install()

        insert = {}
        #models = FileModel.all().add_filter('extension', {'in': (
        #    'bmp', 'gif', 'im', 'jpg', 'jpe', 'jpeg', 'msp',
        #    'pcx', 'png', 'ppm', 'tiff', 'xpm', 'mov'
        #)}).add_filter(
        #    ('orientation',  'orientation'),
        #    ({'null': True}, {'in': range(1, 9)})
        #)
        models = FileModel.all().add_filter('extension', {'in': (
        	'mov'
        )}).add_filter(
            ('orientation',  'orientation'),
            ({'null': True}, {'in': range(1, 9)})
        )
        ImageHelper.join_file_thumbnails(
            models, 'm.%s' % FileModel._pk, width, height, ())
        models.where('tt.thumbnail IS NULL').limit(5)

        for model in models:
            filename = os.path.join(model.abspath(), model.name())
            extension = os.path.splitext(filename)[1][1:]
            thumbname = os.path.join(
				'thumbnails',
				'%sx%s' % (width if width else '', height if height else ''),
				model.name()[0] if len(model.name()) > 0 else '_',
				model.name()[1] if len(model.name()) > 1 else '_',
				model.name()
            )

            if extension == "MOV":
            	thumbfile = os.path.join(basedir, thumbname+".jpg")
            	print "Found Movie: "+filename
            	if not os.path.isfile(thumbfile):
            		directory = os.path.dirname(thumbfile)
            		if not os.path.isdir(directory):
            			os.makedirs(directory)
            		
            		cmdline = [
            		'avconv',
            		'-itsoffset',
            		'-4',
            		'-i',
            		filename,
            		'-vcodec',
            		'mjpeg',
            		'-vframes',
            		'1',
            		'-an',
            		'-f',
            		'rawvideo',
            		'-s',
            		str(width)+"x"+str(height),
            		thumbfile,
				]
            	subprocess.call(cmdline)
            	print "generated thumbfile:"+thumbfile
            	insert[model.id()] = thumbname+".jpg"
            else:
	            thumbfile = os.path.join(basedir, thumbname)            
	            if not os.path.isfile(filename):
	                insert[model.id()] = None
	
	            image = Image.open(filename)
	            if not image:
	                insert[model.id()] = None
	            
	            if not os.path.isfile(thumbfile):
	
	                directory = os.path.dirname(thumbfile)
	                if not os.path.isdir(directory):
	                    os.makedirs(directory)
	
	                rotation = 0.
	                if model.orientation() == 3:
	                    rotation = -180.
	                elif model.orientation() == 6:
	                    rotation = -90.
	                elif model.orientation() == 8:
	                    rotation = -270.
	                if rotation:
	                    image = image.rotate(rotation, expand = 1)
	
	                image = ImageHelper.resize(image, width, height)
	                print (thumbfile)
	                image.save(thumbfile)
	                insert[model.id()] = thumbname
			print "Inserted file:"+thumbname+str(model.id())

        for file_id in insert.keys():
            ImageHelper.add_file_thumbnail(
                file_id, width, height, insert[file_id])

if (__name__ == '__main__'):
    """$ python image.py path/to/database path/to/basedir"""

    if len(sys.argv) < 3:
        exit(1)

    database = sys.argv[1]
    basedir = sys.argv[2]

    if not os.path.isdir(basedir):
        exit(2)

    basedir = os.path.join(basedir, 'cache')

    DBHelper(database)
        
    ImageIndexer.index_file_thumbnails(basedir, 260, 260) #TODO: read from configuration
    ImageIndexer.index_file_thumbnails(basedir, 520, 520) # retina

