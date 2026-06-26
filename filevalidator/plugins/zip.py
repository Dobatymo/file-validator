import re
import zlib
from zipfile import BadZipFile, ZipFile

from ..plug import Filetypes, ValidationResult


@Filetypes.plugin(
    ["zip", "cbz", "pyz", "whl", "egg", "jar", "epub", "xpi", "apk", "odt", "ods", "odp"]
)  # "ipa" uses unsupported compression method
class Zip:
    def __init__(self) -> None:
        pass

    def validate(self, path: str, ext: str, file_size: int, strict: bool = True) -> ValidationResult:
        try:
            with ZipFile(path, "r") as z:
                bad_member = z.testzip()
                if bad_member is not None:
                    return (1, f"CRC check failed for file: {bad_member}")

            return (0, "")
        except BadZipFile as e:
            return (1, str(e))
        except zlib.error as e:
            return (1, str(e))
        except NotImplementedError as e:
            if e.args[0] == "That compression method is not supported":
                return (-1, e.args[0])
            raise
        except RuntimeError as e:
            m = re.match("File '.*' is encrypted, password required for extraction", e.args[0])
            if m is not None:
                return (-1, e.args[0])
            raise
