from typing import Tuple
from zipfile import BadZipFile, ZipFile

from plug import Filetypes


@Filetypes.plugin(["zip", "cbz"])
class Zip:
    def __init__(self) -> None:
        pass

    def validate(self, path: str, ext: str) -> Tuple[int, str]:
        try:
            with ZipFile(path, "r") as z:
                z.testzip()

            return (0, "")
        except BadZipFile as e:
            return (1, str(e))
        except Exception as e:
            return (1, str(e))
