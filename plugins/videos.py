import logging
import os.path
import subprocess
from typing import Tuple

from genutility.filesystem import fileextensions
from genutility.subprocess import force_decode

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
            ret = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
            output = force_decode(ret).strip()
            if output:
                return (1, output)
            else:
                return (0, "")
        except subprocess.CalledProcessError as e:
            logger.error(f"ffmpeg failed for '{path}'")
            output = force_decode(e.output).strip()
            return (1, output)
        # except OSError:
        #    logger.error("calling ffmpeg failed for '{}'".format(path))
