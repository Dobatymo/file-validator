import logging
from typing import Tuple

from genutility.filesystem import fileextensions
from PIL import Image
from pillow_heif import register_avif_opener, register_heif_opener

from plug import Filetypes

logger = logging.getLogger(__name__)


@Filetypes.plugin(fileextensions.images)
class Images:
    def __init__(self) -> None:
        logging.getLogger("PIL.PngImagePlugin").setLevel(logging.WARNING)

        register_avif_opener()
        register_heif_opener()

    def validate(self, path: str, ext: str) -> Tuple[int, str]:
        try:
            with Image.open(path, "r") as img:
                img.load()
            return (0, "")
        except Exception as e:
            return (1, str(e))
