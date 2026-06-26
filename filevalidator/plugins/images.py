import logging
import warnings
from typing import Dict, Optional

from genutility.filesystem import fileextensions
from PIL import Image, ImageSequence, features

from ..limits import DEFAULT_MAX_FILE_SIZE, check_file_size, has_os_error_errno
from ..plug import Filetypes, ValidationResult

logger = logging.getLogger(__name__)


@Filetypes.plugin(fileextensions.images)
class Images:
    def __init__(
        self,
        max_file_size: Optional[int] = DEFAULT_MAX_FILE_SIZE,
        max_file_size_by_extension: Optional[Dict[str, Optional[int]]] = None,
    ) -> None:
        self.max_file_size = max_file_size
        self.max_file_size_by_extension = max_file_size_by_extension

        logging.getLogger("PIL.PngImagePlugin").setLevel(logging.WARNING)

        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=UserWarning)
            if not features.check("avif"):
                from pillow_heif import register_avif_opener

                register_avif_opener()

        from pillow_heif import register_heif_opener

        register_heif_opener()

    def validate(self, path: str, ext: str, file_size: int, strict: bool = True) -> ValidationResult:
        # UserWarning: Corrupt EXIF data.  Expecting to read 2 bytes but only got 0.

        size_result = check_file_size(file_size, ext, self.max_file_size, self.max_file_size_by_extension)
        if size_result:
            return size_result

        try:
            with warnings.catch_warnings(record=strict) as ws:
                warnings.simplefilter("always")
                with Image.open(path, "r") as img:
                    for frame_number, frame in enumerate(ImageSequence.Iterator(img)):
                        try:
                            frame.load()
                        except OSError as e:
                            if has_os_error_errno(e):
                                raise
                            return (1, f"Frame {frame_number}: {e}")
                        except Exception as e:
                            return (1, f"Frame {frame_number}: {e}")
                if ws:
                    return (1, "\n".join(str(w.message) for w in ws))
            return (0, "")
        except OSError as e:
            if has_os_error_errno(e):
                raise
            return (1, str(e))
        except Exception as e:
            return (1, str(e))
