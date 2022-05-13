from typing import Tuple

from genutility.fileformats.srt import MalformedFile, SRTFile

from plug import Filetypes


@Filetypes.plugin(["srt"])
class SRT:
    def __init__(self):
        pass

    def validate(self, path, ext):
        # type: (str, str) -> Tuple[int, str]

        try:
            with SRTFile(path, "r") as fr:
                for sub in fr:
                    pass
            return (0, "")
        except AssertionError as e:
            return (1, str(e))
        except MalformedFile as e:
            return (1, str(e))
