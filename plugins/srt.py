from __future__ import unicode_literals
from plug import Filetypes

from genutility.fileformats.srt import SRTFile, MalformedFile

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
        except MalformedFile as e:
            return (1, str(e))
