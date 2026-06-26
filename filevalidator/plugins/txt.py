from ..plug import Filetypes, ValidationResult


@Filetypes.plugin(["txt"])
class TXT:
    """Trivial plugin to validate .txt files. It assumes all txt files are valid.
    ["txt"] determins the list of file extensions this plugin can handle."""

    def __init__(self) -> None:
        """Constructor is called once per program run."""

    def validate(self, path: str, ext: str, file_size: int, strict: bool = True) -> ValidationResult:
        """validate() is called for every file
        path: complete/path/to/file.exe
        ext: just the extension of the file e.g. "exe"
        file_size: size captured by the scanner immediately before validation

        Should return (0, "") if everything is fine,
        or (1, error_msg_string) if errors were found."""
        return (0, "")
