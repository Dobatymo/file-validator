from typing import Dict, Optional

from bs4 import BeautifulSoup
from genutility.file import read_file

from ..limits import DEFAULT_MAX_FILE_SIZE, check_file_size
from ..plug import Filetypes, ValidationResult


@Filetypes.plugin(["htm", "html"])
class HTML:
    def __init__(
        self,
        max_file_size: Optional[int] = DEFAULT_MAX_FILE_SIZE,
        max_file_size_by_extension: Optional[Dict[str, Optional[int]]] = None,
    ) -> None:
        self.max_file_size = max_file_size
        self.max_file_size_by_extension = max_file_size_by_extension

    def validate(self, path: str, ext: str, file_size: int, strict: bool = True) -> ValidationResult:
        size_result = check_file_size(file_size, ext, self.max_file_size, self.max_file_size_by_extension)
        if size_result:
            return size_result

        try:
            data = read_file(path, "rb")
            BeautifulSoup(data, "lxml")
            return (0, "")
        except OSError:
            raise
        except Exception as e:
            return (1, str(e.__class__.__name__) + ": " + str(e))
