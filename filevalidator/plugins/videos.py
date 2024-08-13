import logging
import subprocess
from shutil import which
from typing import Tuple

from genutility.filesystem import fileextensions
from genutility.subprocess import force_decode

from ..plug import Filetypes, PluginError

logger = logging.getLogger(__name__)


@Filetypes.plugin(fileextensions.video)
class Videos:
    def __init__(self, ffmpeg_binary: str = "ffmpeg") -> None:
        _binary = which(ffmpeg_binary)
        if _binary is None:
            raise PluginError("Cannot find ffmpeg binary executable")
        else:
            self.ffmpeg_binary = _binary

    def validate(self, path: str, ext: str, strict: bool = True) -> Tuple[int, str]:
        cmd = [self.ffmpeg_binary, "-v", "error", "-nostats", "-i", path, "-f", "null", "-"]
        try:
            ret = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
            output = force_decode(ret).strip()
            if output:
                return (1, output)
            else:
                return (0, "")
        except subprocess.CalledProcessError as e:
            logger.error("ffmpeg failed for `%s`", path)
            output = force_decode(e.output).strip()
            return (1, output)
        # except OSError:
        #    logger.error("calling ffmpeg failed for '{}'".format(path))
