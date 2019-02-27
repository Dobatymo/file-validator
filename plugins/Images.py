from __future__ import unicode_literals
import os, os.path, logging, re

from PIL import Image

from plug import Filetypes

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

@Filetypes.plugin(["jpg", "jpeg", "bmp", "png", "gif", "tga", "tiff", "tif"])
class Images(object):
    def __init__(self):
        pass

    def validate(self, path, ext):
        try:
            Image.open(path).save("temp/validate_images_temp.png") #use .verify()
            return (0, "")
        except Exception as e:
            return (1, str(e))
