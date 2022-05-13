from typing import Tuple
from zipfile import ZipFile

try:
    from zipfile import BadZipFile
except ImportError:
    from zipfile import BadZipfile as BadZipFile

from plug import Filetypes


@Filetypes.plugin(["zip", "cbz"])
class Zip:
    def __init__(self):
        pass

    def validate(self, path, ext):
        # type: (str, str) -> Tuple[int, str]

        try:
            with ZipFile(path, "r") as z:
                z.testzip()

            return (0, "")
        except BadZipFile as e:
            return (1, str(e))
        except Exception as e:
            return (1, str(e))
