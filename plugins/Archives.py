from __future__ import unicode_literals
import sys, logging, subprocess
from .rar import Rar, RarError # use 'pip install rarfile' module instead ?

from plug import Filetypes
from genutility.twothree.filesystem import tofs, fromfs

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

@Filetypes.plugin(["zip", "cbz", "7z", "gz", "bz2", "z", "tar", "tgz", "tbz", "rar", "cbr"])
class Archives(object):

    def __init__(self, UnRarExecutable, SevenZipExecutable):
        self.UnRarExecutable = UnRarExecutable
        self.SevenZipExecutable = SevenZipExecutable

    def validate(self, path, ext):
        foundexe = True
        if ext in ("zip", "cbz", "7z", "gz", "bz2", "z", "tar", "tgz", "tbz"):
            Executable = self.SevenZipExecutable
            args = "t -p-"
        elif ext in ("rar", "cbr"):
            Executable = self.UnRarExecutable
            #args = u"t -p-"
            foundexe = False
            r = Rar(path, Executable)
            try:
                r.test()
                return (0, "")
            except RarError as e:
                return (1, "{} [{}] [{}]: {}".format(str(e), e.cmd, e.returncode, e.output))
        else:
            foundexe = False

        if foundexe:
            try:
                cmd = '"{}" {} "{}"'.format(Executable, args, path)
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
