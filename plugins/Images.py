from __future__ import unicode_literals
import os, os.path, logging, re
import Image

from plug import Filetypes

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

@Filetypes.plugin(["jpg", "jpeg", "bmp", "png", "gif", "tga", "tiff", "tif"])
class Images(object):
    def __init__(self):
        self.covertbmp = True
        self.coverttiff = True
        self.convertpath = re.compile(r"^.:/PUBLIC/.*$")

    def copy_time(self, src, dst):
        t = os.path.getmtime(src)
        os.utime(dst, (t, t))

    def validate(self, path, ext):
        try:
            Image.open(path).save("temp/validate_images_temp.png") #use .verify()
        except Exception as e:
            return (1, str(e))

        if ext == "bmp" and self.covertbmp and self.convertpath.match(path):
            pngfile = os.path.splitext(path)[0] + ".png"
            if not os.path.exists(pngfile):
                Image.open(path).save(pngfile)
                self.copy_time(path, pngfile)
                os.remove(path)
                logger.info("Coverted: " + path + "\n-> " + pngfile)
        if ext == "tif" and self.coverttiff and self.convertpath.match(path):
            pngfile = os.path.splitext(path)[0] + ".png"
            if not os.path.exists(pngfile):
                im = Image.open(path)
                if im.info["compression"] == "raw":
                    im.save(pngfile)
                    del im
                    self.copy_time(path, pngfile)
                    os.remove(path)
                    logger.info("Coverted: " + path + "\n-> " + pngfile)
                elif im.info["compression"] == "tiff_lzw":
                    pass #already losslessly compressed
                else:
                    print(im.info)
                    del im
                    exit("Unknown TIFF Compression")
        
        return (0, "")
