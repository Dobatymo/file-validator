import logging
import subprocess
from typing import Tuple

from genutility.subprocess import force_decode

from plug import Filetypes

logger = logging.getLogger(__name__)


@Filetypes.plugin(["flac"])
class FLAC:
    def __init__(self, executable: str, warnings_as_errors: bool = True) -> None:
        self.executable = executable
        self.wae = warnings_as_errors

    def validate(self, path: str, ext: str) -> Tuple[int, str]:
        try:
            if self.wae:
                cmd = f'"{self.executable}" -t -s -w "{path}"'
            else:
                cmd = f'"{self.executable}" -t -s "{path}"'
            subprocess.check_output(cmd, stderr=subprocess.STDOUT)
            return (0, "")
        except subprocess.CalledProcessError as e:
            output = force_decode(e.output).strip()
            return (1, output)
