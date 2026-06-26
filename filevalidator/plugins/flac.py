import logging
import platform
from shutil import which
from typing import Optional

from genutility._files import to_dos_path

from ..limits import CommandError, CommandTimeout, run_command, timeout_result
from ..plug import Filetypes, PluginError, ValidationResult

logger = logging.getLogger(__name__)

_is_win = platform.system() == "Windows"


@Filetypes.plugin(["flac"])
class FLAC:
    def __init__(self, flac_binary: str = "flac", timeout: Optional[float] = 3600) -> None:
        self.timeout = timeout
        _binary = which(flac_binary)
        if _binary is None:
            raise PluginError("Cannot find flac binary executable")
        else:
            self.flac_binary = _binary

    def validate(self, path: str, ext: str, file_size: int, strict: bool = True) -> ValidationResult:
        if _is_win:
            path = to_dos_path(path)

        try:
            if strict:
                cmd = [self.flac_binary, "-t", "-s", "-w", path]
            else:
                cmd = [self.flac_binary, "-t", "-s", path]
            run_command(cmd, self.timeout)
            return (0, "")
        except CommandError as e:
            return (1, e.output)
        except CommandTimeout as e:
            return timeout_result(cmd, self.timeout, e.output)
