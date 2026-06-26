from defusedxml.ElementTree import ParseError, parse

from ..plug import Filetypes, ValidationResult


@Filetypes.plugin(["xml", "xsl", "svg", "rss", "atom", "plist", "musicxml", "dupeguru", "dupegurudirs"])
class XML:
    def __init__(self) -> None:
        pass

    def validate(self, path: str, ext: str, file_size: int, strict: bool = True) -> ValidationResult:
        try:
            parse(path)
            return (0, "")
        except ParseError as e:
            return (1, str(e))
        except OSError:
            raise
        except Exception as e:
            return (1, str(e))
