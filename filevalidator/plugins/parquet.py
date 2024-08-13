from typing import Tuple

import pyarrow.parquet as pq
from pyarrow.lib import ArrowInvalid

from ..plug import Filetypes


@Filetypes.plugin(["parquet"])
class Parquet:
    def __init__(self) -> None:
        pass

    def validate(self, path: str, ext: str, strict: bool = True) -> Tuple[int, str]:
        try:
            pq.read_table(path)
            return (0, "")
        except ArrowInvalid as e:
            return (1, str(e))
