from __future__ import unicode_literals
import sys, logging, subprocess

from plug import Filetypes
from genutility.twothree.filesystem import tofs

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

@Filetypes.plugin(["flac"])
class FLAC(object):

    def __init__(self, executable, warnings_as_errors=True):
        self.executable = executable
        self.wae = warnings_as_errors
    
    def validate(self, path, ext):
        try:
            if self.wae:
                cmd = '"{}" -t -s -w "{}"'.format(self.executable, path)
            else:
                cmd = '"{}" -t -s "{}"'.format(self.executable, path)
            ret = subprocess.check_output(tofs(cmd), stderr=subprocess.STDOUT)
            return (0, "")
        except subprocess.CalledProcessError as e:
            return (1, e.output.decode(sys.stdout.encoding))
