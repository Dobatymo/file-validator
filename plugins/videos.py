import logging
import os.path
import subprocess
import sys
from typing import Tuple

from genutility.filesystem import fileextensions

from plug import Filetypes

logger = logging.getLogger(__name__)


@Filetypes.plugin(fileextensions.video)
class Videos:
    def __init__(self, ffmpeg: str) -> None:
        self.ffmpeg = ffmpeg

        if not os.path.isfile(ffmpeg):
            raise RuntimeError("Cannot find ffmpeg executable")

    def validate(self, path: str, ext: str) -> Tuple[int, str]:
        cmd = [self.ffmpeg, "-v", "error", "-nostats", "-i", path, "-f", "null", "-"]
        try:
            output = subprocess.check_output(cmd, stderr=subprocess.STDOUT).decode(sys.stdout.encoding)
            if output:
                return (1, output)
            else:
                return (0, "")
        except subprocess.CalledProcessError as e:
            logger.error(f"ffmpeg failed for '{path}'")
            return (1, e.output.decode(sys.stdout.encoding))
        # except OSError:
        #    logger.error("calling ffmpeg failed for '{}'".format(path))
