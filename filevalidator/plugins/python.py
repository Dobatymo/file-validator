from typing import Dict, Optional

from ..limits import DEFAULT_MAX_FILE_SIZE, check_file_size
from ..plug import Filetypes, ValidationResult


@Filetypes.plugin(["py", "pyw"])
class Python:
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
            with open(path, "rb") as fr:
                compile(fr.read(), "<file>", "exec")
            return (0, "")
        except (SyntaxError, TypeError) as e:
            return (1, str(e))
        except ValueError as e:  # source code string cannot contain null bytes
            return (1, str(e))
