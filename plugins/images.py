import logging
from typing import Tuple

from genutility.filesystem import fileextensions
from PIL import Image

from plug import Filetypes

logger = logging.getLogger(__name__)


@Filetypes.plugin(fileextensions.images)
class Images:
    def __init__(self):
        logging.getLogger("PIL.PngImagePlugin").setLevel(logging.WARNING)

    def validate(self, path, ext):
        # type: (str, str) -> Tuple[int, str]

        try:
            Image.open(path).save("temp/validate_images_temp.png")  # use .verify()
            return (0, "")
        except Exception as e:
            return (1, str(e))
