from __future__ import absolute_import, division, print_function, unicode_literals

import logging
import os.path
import subprocess
import sys

from genutility.filesystem import fileextensions
from genutility.twothree.filesystem import tofs

from plug import Filetypes

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

@Filetypes.plugin(fileextensions.video)
class Videos(object):

    def __init__(self, ffmpeg):
        self.ffmpeg = ffmpeg

        if not os.path.isfile(ffmpeg):
            raise RuntimeError("Cannot find ffmpeg executable")

    def validate(self, path, ext):
        cmd = [self.ffmpeg, "-v", "error", "-nostats", "-i", path, "-f", "null", "-"]
        try:
            output = subprocess.check_output(cmd, stderr=subprocess.STDOUT).decode(sys.stdout.encoding)
            if output:
                return (1, output)
            else:
                return (0, "")
        except subprocess.CalledProcessError as e:
            logger.error("ffmpeg failed for '{}'".format(path))
            return (1, e.output.decode(sys.stdout.encoding))
        #except OSError:
        #    logger.error("calling ffmpeg failed for '{}'".format(path))
