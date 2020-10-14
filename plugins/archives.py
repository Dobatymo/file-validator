from __future__ import unicode_literals

import logging
import subprocess
import sys
from pathlib import Path

from genutility.fileformats.rar import Rar, RarError  # use 'pip install rarfile' module instead ?
from genutility.filesystem import fileextensions
from genutility.twothree.filesystem import tofs

from plug import Filetypes

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

extensions = set(fileextensions.archives + fileextensions.image_archives + fileextensions.compressed) - set(["zip", "cbz"]) # zip handled by zip.py

@Filetypes.plugin(extensions)
class Archives(object):

    def __init__(self, UnRarExecutable, SevenZipExecutable):
        self.UnRarExecutable = Path(UnRarExecutable)
        self.SevenZipExecutable = Path(SevenZipExecutable)

    def validate(self, path, ext):
        foundexe = True
        if ext in ("cb7", "cbt", "cba", "7z", "gz", "bz2", "xz", "z", "lzma", "tar", "tgz", "tbz", "cab"):
            executable = self.SevenZipExecutable
            args = "t -p-"
        elif ext in ("rar", "cbr"):
            executable = self.UnRarExecutable
            #args = u"t -p-"
            foundexe = False
            r = Rar(path, executable)
            try:
                r.test()
                return (0, "")
            except RarError as e:
                return (1, "{} [{}] [{}]: {}".format(str(e), e.cmd, e.returncode, e.output))
        elif ext in {"wim"}:
            # "C:\Program Files (x86)\Windows Kits\10\Tools\bin\i386\imagex.exe" /info "C:\Windows\Containers\WindowsDefenderApplicationGuard.wim" /check
            foundexe = False
        else:
            foundexe = False

        if foundexe:
            try:
                cmd = '"{}" {} "{}"'.format(executable, args, path)
                ret = subprocess.check_output(tofs(cmd))
                return (0, "")
            except UnicodeEncodeError as e:
                print("UnicodeEncodeError")
            except subprocess.CalledProcessError as e:
                try:
                    output = e.output.decode(sys.stdout.encoding).replace("\n\n", "\n")
                    return (1, "{} [{}] [{}]: {}".format(str(e), e.cmd, e.returncode, output))
                except UnicodeDecodeError:
                    logger.exception(path)
