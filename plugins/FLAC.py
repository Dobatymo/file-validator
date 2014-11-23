from __future__ import unicode_literals
import sys, logging, subprocess

from plug import Filetypes

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

@Filetypes.plugin(["flac"])
class FLAC(object):

    executable = "D:/SYSTEM/Programs (x86)/FLAC v1.3.0/flac.exe"

    def __init__(self):
        pass
    
    def validate(self, path, ext):
        try:
            cmd = '"{}" -t -s -w "{}"'.format(self.executable, path)
            ret = subprocess.check_output(cmd.encode(sys.getfilesystemencoding()), stderr=subprocess.STDOUT)
            return (0, "")
        except subprocess.CalledProcessError as e:
            return (1, e.output.decode(sys.stdout.encoding))
