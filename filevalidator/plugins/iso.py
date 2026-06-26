import os
from typing import Dict, Optional

from pycdlib import PyCdlib
from pycdlib.pycdlibexception import PyCdlibInvalidISO

from ..limits import DEFAULT_MAX_FILE_SIZE, check_file_size
from ..plug import Filetypes, ValidationResult


@Filetypes.plugin(["iso"])
class Iso:
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

        iso = PyCdlib()

        try:
            iso.open(path)
            try:
                logical_block_size = iso.pvd.logical_block_size()
                expected_volume_size = iso.pvd.space_size * logical_block_size
                if file_size < expected_volume_size:
                    return (
                        1,
                        f"ISO is truncated: expected at least {expected_volume_size} bytes, got {file_size}",
                    )

                for basepath, _dirlist, filelist in iso.walk(iso_path="/"):
                    for filename in filelist:
                        iso_path = f"{basepath}/{filename}"
                        record = iso.get_record(iso_path=iso_path)
                        if not record.is_symlink() and record.is_file():
                            data_length = record.get_data_length()
                            data_end = record.extent_location() * logical_block_size + data_length
                            if data_end > file_size:
                                return (
                                    1,
                                    f"{iso_path} extends past the end of the ISO: "
                                    f"data ends at {data_end}, file size is {file_size}",
                                )

                            with open(os.devnull, "wb") as fw:
                                iso.get_file_from_iso_fp(fw, iso_path=iso_path)
                                # This comparison alone cannot detect every truncation because pycdlib may adjust
                                # the record data length to the available data. The volume and extent checks above
                                # therefore use the original file size as the independent boundary.
                                if data_length != fw.tell():
                                    return (
                                        1,
                                        f"{iso_path} is truncated. expected {data_length} vs actual {fw.tell()}",
                                    )
                return (0, "")
            finally:
                iso.close()
        except PyCdlibInvalidISO as e:
            message = str(e)
            return (1, message)
