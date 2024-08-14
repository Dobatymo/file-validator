import logging
import platform
import subprocess
from shutil import which
from typing import Tuple

from genutility._files import to_dos_path
from genutility.subprocess import force_decode

from ..plug import Filetypes, PluginError

logger = logging.getLogger(__name__)

_is_win = platform.system() == "Windows"


@Filetypes.plugin(["flac"])
class FLAC:
    def __init__(self, flac_binary: str = "flac") -> None:
        _binary = which(flac_binary)
        if _binary is None:
            raise PluginError("Cannot find flac binary executable")
        else:
            self.flac_binary = _binary

    def validate(self, path: str, ext: str, strict: bool = True) -> Tuple[int, str]:
        if _is_win:
            path = to_dos_path(path)

        try:
            if strict:
                cmd = [self.flac_binary, "-t", "-s", "-w", path]
            else:
                cmd = [self.flac_binary, "-t", "-s", path]
            subprocess.check_output(cmd, stderr=subprocess.STDOUT)
            return (0, "")
        except subprocess.CalledProcessError as e:
            output = force_decode(e.output).strip()
            return (1, output)
