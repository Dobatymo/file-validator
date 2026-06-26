import pyarrow.parquet as pq
from pyarrow.lib import ArrowException

from ..limits import has_os_error_errno
from ..plug import Filetypes, ValidationResult


@Filetypes.plugin(["parquet"])
class Parquet:
    def __init__(self) -> None:
        pass

    def validate(self, path: str, ext: str, file_size: int, strict: bool = True) -> ValidationResult:
        try:
            parquet_file = pq.ParquetFile(path)
            for _batch in parquet_file.iter_batches():
                pass
            return (0, "")
        except ArrowException as e:
            return (1, str(e))
        except OSError as e:
            if has_os_error_errno(e):
                raise
            return (1, str(e))
