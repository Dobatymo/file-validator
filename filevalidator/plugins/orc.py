from pyarrow import orc
from pyarrow.lib import ArrowException

from ..limits import has_os_error_errno
from ..plug import Filetypes, ValidationResult


@Filetypes.plugin(["orc"])
class ORC:
    def __init__(self) -> None:
        pass

    def validate(self, path: str, ext: str, file_size: int, strict: bool = True) -> ValidationResult:
        try:
            orc_file = orc.ORCFile(path)
            for i in range(orc_file.nstripes):
                orc_file.read_stripe(i)
            return (0, "")
        except ArrowException as e:
            return (1, str(e))
        except OSError as e:
            if has_os_error_errno(e):
                raise
            return (1, str(e))
