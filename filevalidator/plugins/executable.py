import pefile

from ..plug import Filetypes, ValidationResult


@Filetypes.plugin(["exe", "dll", "sys"])
class Executable:
    def __init__(self, fast_load: bool = False) -> None:
        self.fast_load = fast_load

    def validate(self, path: str, ext: str, file_size: int, strict: bool = True) -> ValidationResult:
        try:
            with pefile.PE(path, fast_load=self.fast_load):
                pass
            return (0, "")
        except OSError:
            raise
        except Exception as e:
            return (1, str(e))
