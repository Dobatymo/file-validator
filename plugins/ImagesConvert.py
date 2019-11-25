from __future__ import unicode_literals
import os, os.path, logging, re

from PIL import Image, TiffImagePlugin

from genutility.stdio import errorquit, waitcontinue

from plug import Filetypes

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

@Filetypes.plugin(["jpg", "jpeg", "bmp", "png", "gif", "tga", "tiff", "tif"])
class ImagesConvert(object):
    def __init__(self):
        self.covertbmp = True
        self.coverttiff = True
        self.convertpath = re.compile(r"^.:\\PUBLIC\\.*$")

    def copy_time(self, src, dst):
        t = os.path.getmtime(src)
        os.utime(dst, (t, t))

    def validate(self, path, ext):
        try:
            if self.convertpath.match(path):
                logging.debug("{} matched".format(path))
                if self.covertbmp and ext == "bmp":
                    Image.open(path).save("temp/validate_images_temp.png") #use .verify()
                    pngfile = os.path.splitext(path)[0] + ".png"
                    if not os.path.exists(pngfile):
                        Image.open(path).save(pngfile, compress_level=9)
                        self.copy_time(path, pngfile)
                        os.remove(path)
                        logger.info("Coverted: " + path + "\n-> " + pngfile)
                elif self.coverttiff and (ext == "tif" or ext == "tiff"):
                    newpath = path + ".new"
                    if not os.path.exists(newpath):
                        im = Image.open(path)
                        if im.info["compression"] == "raw":
                            #[None, "tiff_ccitt", "group3", "group4", "tiff_jpeg", "tiff_adobe_deflate", "tiff_thunderscan", "tiff_deflate", "tiff_sgilog", "tiff_sgilog24", "tiff_raw_16"]
                            im.save(newpath, "tiff", compression = "tiff_lzw") #loses metadata
                            del im
                            self.copy_time(path, newpath)
                            #os.remove(path)
                            #os.rename(newpath, path)
                            logger.info("Coverted: " + path + "\n-> " + newpath)
                        elif im.info["compression"] == "tiff_lzw":
                            logging.debug("{} already compressed".format(path))
                        else:
                            print(im.info)
                            del im
                            errorquit("Unknown TIFF Compression")
            else:
                logging.debug("{} doesn't match".format(path))
            return (0, "")
        except Exception as e:
            waitcontinue("Conversion failed")
            return (1, str(e))
