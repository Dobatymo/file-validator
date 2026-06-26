from genutility.fileformats.srt import MalformedFile, SRTFile

from ..plug import Filetypes, ValidationResult


@Filetypes.plugin(["srt"])
class SRT:
    def __init__(self) -> None:
        pass

    def validate(self, path: str, ext: str, file_size: int, strict: bool = True) -> ValidationResult:
        try:
            with SRTFile(path, "r") as fr:
                for _sub in fr:
                    pass
            return (0, "")
        except AssertionError as e:
            return (1, str(e))
        except MalformedFile as e:
            return (1, str(e))
