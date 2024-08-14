import os
from typing import Tuple

from pycdlib import PyCdlib
from pycdlib.pycdlibexception import PyCdlibInvalidISO

from ..plug import Filetypes


@Filetypes.plugin(["iso"])
class Iso:
    def __init__(self) -> None:
        pass

    def validate(self, path: str, ext: str, strict: bool = True) -> Tuple[int, str]:
        iso = PyCdlib()

        try:
            iso.open(path)
            try:
                for basepath, _dirlist, filelist in iso.walk(iso_path="/"):
                    for filename in filelist:
                        path = f"{basepath}/{filename}"
                        record = iso.get_record(iso_path=path)
                        if not record.is_symlink() and record.is_file():
                            with open(os.devnull, "wb") as fw:
                                iso.get_file_from_iso_fp(fw, iso_path=path)
                                if (
                                    record.get_data_length() != fw.tell()
                                ):  # todo: doesn't work yet. pycdlib "fixes" the filesize of truncated isos
                                    return (
                                        1,
                                        f"{path} is truncated. expected {record.get_data_length()} vs actual {fw.tell()}",
                                    )
                return (0, "")
            finally:
                iso.close()
        except PyCdlibInvalidISO as e:
            print(str(e))
            return (1, str(e))
