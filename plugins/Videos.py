from __future__ import unicode_literals
import sys, subprocess, logging

from plug import Filetypes

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

@Filetypes.plugin(["avi", "mkv", "webm", "mp4", "m4v", "ogm", "ogv", "wmv", "divx", "asf", "nsv", "mpg", "vob", "flv", "f4v", "mov", "rm", "rmvb"])
class Videos(object):

    ffmpeg = "D:/SYSTEM/Programs (x64)/FFmpeg/bin/ffmpeg.exe"

    def __init__(self):
        pass
    
    def validate(self, path, ext):
        cmd = "{path} -v error -nostats -i \"{filename}\" -f null -"
        try:
            output = subprocess.check_output(cmd.format(path=self.ffmpeg, filename=path).encode(sys.getfilesystemencoding()), stderr=subprocess.STDOUT)
            if output:
                return (1, output)
            else:
                return (0, "")
        except subprocess.CalledProcessError as e:
            logger.error("ffmpeg failed for '{}'".format(path))
