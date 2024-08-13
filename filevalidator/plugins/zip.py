import re
from typing import Tuple
from zipfile import BadZipFile, ZipFile

from ..plug import Filetypes


@Filetypes.plugin(
    ["zip", "cbz", "pyz", "whl", "egg", "jar", "epub", "xpi", "apk", "odt", "ods", "odp"]
)  # "ipa" uses unsupported compression method
class Zip:
    def __init__(self) -> None:
        pass

    def validate(self, path: str, ext: str, strict: bool = True) -> Tuple[int, str]:
        try:
            with ZipFile(path, "r") as z:
                z.testzip()

            return (0, "")
        except BadZipFile as e:
            return (1, str(e))
        except RuntimeError as e:
            m = re.match("File '.*' is encrypted, password required for extraction", e.args[0])
            if m is not None:
                return (-1, e.args[0])
            raise
