from __future__ import unicode_literals
from plug import Filetypes

from Utilities.srt import SRTFile, MalformedFileException

@Filetypes.plugin(["srt"])
class SRT(object):
    def __init__(self):
        pass
    
    def validate(self, path, ext):
        try:
            with SRTFile(path, "r") as fr:
                for sub in fr:
                    pass
            return (0, "")
        except AssertionError as e:
            return (1, str(e))
        except MalformedFileException as e:
            return (1, str(e))
