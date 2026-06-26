import logging
import os
from shutil import which
from typing import Optional

from genutility.filesystem import fileextensions

from ..limits import CommandError, CommandTimeout, run_command, timeout_result
from ..plug import Filetypes, PluginError, ValidationResult

logger = logging.getLogger(__name__)


@Filetypes.plugin(fileextensions.video)
class Videos:
    def __init__(self, ffmpeg_binary: Optional[str] = None, timeout: Optional[float] = 3600) -> None:
        self.timeout = timeout
        binary = ffmpeg_binary or os.environ.get("FFMPEG_BINARY") or "ffmpeg"
        _binary = which(binary)
        if _binary is None:
            raise PluginError("Cannot find ffmpeg binary executable")
        else:
            self.ffmpeg_binary = _binary

    def validate(self, path: str, ext: str, file_size: int, strict: bool = True) -> ValidationResult:
        cmd = [self.ffmpeg_binary, "-v", "error", "-nostats", "-i", path, "-f", "null", "-"]
        try:
            output = run_command(cmd, self.timeout)
            if output:
                return (1, output)
            else:
                return (0, "")
        except CommandError as e:
            logger.error("ffmpeg failed for `%s`", path)
            return (1, e.output)
        except CommandTimeout as e:
            return timeout_result(cmd, self.timeout, e.output)
