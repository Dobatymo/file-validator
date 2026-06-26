from ..plug import Filetypes, ValidationResult


@Filetypes.plugin(["m3u8"])
class M3U8:
    def __init__(self) -> None:
        pass

    def validate(self, path: str, ext: str, file_size: int, strict: bool = True) -> ValidationResult:
        try:
            with open(path, encoding="utf-8") as fr:
                for _line in fr:
                    pass
            return (0, "")
        except UnicodeDecodeError as e:
            return (1, f"UnicodeDecodeError: {e}")
