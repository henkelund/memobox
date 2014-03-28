import sys, os
import subprocess
from PIL import Image
from helper.db import DBHelper, DBSelect
from helper.image import ImageHelper
from model.file import FileModel
from helper.log import LogHelper as logger
from model.device import DeviceModel

class ImageIndexer(object):
    """Class responsible for generating thumbnails"""

    @classmethod
    def index_file_thumbnails(cls, basedir, width, height):
        """Generate thumbnails for image files"""

        ImageHelper.install()

        insert = {}
        cols = [
        '_id',
        'type',
        'subtype',
        'name'
        ]

        models = FileModel.all().add_filter('extension', {'in': (
            'bmp', 'gif', 'im', 'jpg', 'jpe', 'jpeg', 'msp',
            'pcx', 'png', 'ppm', 'tiff', 'xpm', 'mov'
        )}).add_filter(
            ('orientation',  'orientation'),
            ({'null': True}, {'in': range(0, 9)})
        )

        ImageHelper.join_file_thumbnails(
            models, 'm.%s' % FileModel._pk, width, height, ())
        models.where('tt.thumbnail IS NULL').limit(70).order('created_at', 'DESC')
        
        for model in models:
            filename = os.path.join(model.abspath(), model.name())
            extension = os.path.splitext(filename)[1][1:]

            print filename
                        
            thumbname = os.path.join(
				'thumbnails',
				'%sx%s' % (width if width else '', height if height else ''),
				model.name()[0] if len(model.name()) > 0 else '_',
				model.name()[1] if len(model.name()) > 1 else '_',
				model.name()
            )

            if (extension == "MOV") or (extension == "mov") :
            	thumbfile = os.path.join(basedir, thumbname+".jpg")
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
            		insert[model.id()] = thumbname+".jpg"
            else:
            	thumbfile = os.path.join(basedir, thumbname+"_"+str(model.id())+".jpg")
            	print "Thumbfile: "+thumbfile
            	directory = os.path.dirname(thumbfile)
            	if not os.path.isdir(directory):
            		os.makedirs(directory)
        		
            	cmdline = [
            	'gm',
            	'convert',
            	'-size',
            	str(width)+"x"+str(height),
            	filename,
            	'-thumbnail',
            	str(width)+"x"+str(height)+"^",
            	'-gravity',
            	'center',
            	'-extent',
            	str(width)+"x"+str(height),
            	'+profile',
            	'"*"',
            	'-auto-orient',
            	thumbfile
			]
            	subprocess.call(cmdline)
            	insert[model.id()] = thumbname+"_"+str(model.id())+".jpg"

        print "Add generated thumbnails to database"
        for file_id in insert.keys():
            ImageHelper.add_file_thumbnail(
                file_id, width, height, insert[file_id])
                
        print "Image index done"

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

    for device in DeviceModel.all():
    	states = { -1 : 'Error', 1 : 'Preparing', 2 : 'Transfering files', 3 : 'Preparing images', 4 : 'Ready' }
    	images = DBSelect('device','count(*) as imagecount').join('file', 'device._id = file.device', None).where("device._id = "+str(device.id())).where("file.extension = 'jpg'").query()
    	thumbnails = DBSelect('device','count(*) as thumbnailcount').join('file', 'device._id = file.device', None).join('file_thumbnail', 'file_thumbnail.file = file._id', None).where("device._id = "+str(device.id())).where("file.extension = 'jpg'").query()

    	imagecount = 0
    	thumbnailcount = 0; 
    	
    	for image in images:
    		imagecount = image['imagecount']

    	for thumbnail in thumbnails:
    		thumbnailcount = thumbnail['thumbnailcount']
    	    	
    	if(device.state() != 4 and imagecount == thumbnailcount):
    		DBSelect('device').where('device._id = '+str(device.id())).query_update({ 'state' : 4 });
    		#args = ['sudo','sqlite3', '/HDD/index.db', 'UPDATE device SET state = 4 WHERE _id > 0']
    		#call(args)
    		#print(" ".join(args))
    		#device.state(4)
    		#device.save()