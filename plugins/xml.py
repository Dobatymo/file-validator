from typing import Tuple

from defusedxml.ElementTree import ParseError, parse

from plug import Filetypes


@Filetypes.plugin(["xml", "xsl"])
class XML:
    def __init__(self) -> None:
        pass

    def validate(self, path: str, ext: str) -> Tuple[int, str]:
        try:
            parse(path)
            return (0, "")
        except ParseError as e:
            return (1, str(e))
        except Exception as e:
            return (1, str(e))
