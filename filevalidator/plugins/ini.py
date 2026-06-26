import configparser

from ..plug import Filetypes, ValidationResult


@Filetypes.plugin(["ini"])
class INI:
    def __init__(self) -> None:
        pass

    def validate(self, path: str, ext: str, file_size: int, strict: bool = True) -> ValidationResult:
        try:
            config = configparser.ConfigParser()
            # Use the locale default on purpose: INI files are often written in the local encoding, and
            # running Python in UTF-8 mode can change that default.
            with open(path, encoding=None) as fr:
                config.read_file(fr)
            return (0, "")
        except (UnicodeDecodeError, configparser.Error) as e:
            return (1, str(e))
