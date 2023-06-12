from typing import Tuple

from bs4 import BeautifulSoup
from genutility.file import read_file

from plug import Filetypes


@Filetypes.plugin(["htm", "html"])
class HTML:
    def __init__(self) -> None:
        pass

    def validate(self, path: str, ext: str) -> Tuple[int, str]:
        try:
            data = read_file(path, "rb")
            BeautifulSoup(data, "lxml")
            return (0, "")
        except Exception as e:
            return (1, str(e.__class__.__name__) + ": " + str(e))
