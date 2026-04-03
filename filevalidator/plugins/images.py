import logging
import warnings
from typing import Tuple

from genutility.filesystem import fileextensions
from PIL import Image, features

from ..plug import Filetypes

logger = logging.getLogger(__name__)


@Filetypes.plugin(fileextensions.images)
class Images:
    def __init__(self) -> None:
        logging.getLogger("PIL.PngImagePlugin").setLevel(logging.WARNING)

        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=UserWarning)
            if not features.check("avif"):
                from pillow_heif import register_avif_opener

                register_avif_opener()

        from pillow_heif import register_heif_opener

        register_heif_opener()

    def validate(self, path: str, ext: str, strict: bool = True) -> Tuple[int, str]:
        # UserWarning: Corrupt EXIF data.  Expecting to read 2 bytes but only got 0.

        try:
            with warnings.catch_warnings(record=strict) as ws:
                warnings.simplefilter("always")
                with Image.open(path, "r") as img:
                    img.load()
                if ws:
                    return (1, "\n".join(str(w.message) for w in ws))
            return (0, "")
        except Exception as e:
            return (1, str(e))
