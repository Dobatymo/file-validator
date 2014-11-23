from __future__ import unicode_literals
import sys, logging, subprocess
from rar import Rar, RarError

from plug import Filetypes

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

@Filetypes.plugin(["zip", "cbz", "7z", "gz", "bz2", "z", "tar", "tgz", "tbz", "rar", "cbr"])
class Archives(object):

    def __init__(self, UnRarExecutable="C:/Program Files/WinRAR/UnRAR.exe",
        SevenZipExecutable="C:/Program Files/7-Zip/7z.exe"):
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
                return (1, "{}: {} {}".format(e.returncode, str(e), e.output))
        else:
            foundexe = False

        if foundexe:
            try:
                cmd = '"{}" {} "{}"'.format(Executable, args, path)
                ret = subprocess.check_output(cmd.encode(sys.getfilesystemencoding()))
                return (0, "")
            except UnicodeEncodeError as e:
                print("UnicodeEncodeError")
            except subprocess.CalledProcessError as e:
                try:
                    output = e.output.decode(sys.stdout.encoding).replace("\n\n", "\n")
                    return (1, "{}: {} {}".format(e.returncode, str(e), output))
                except UnicodeDecodeError as e:
                    logger.exception(path)

"""255 	USER BREAK 	User stopped the process

9
	CREATE ERROR 	Create file error
8 	MEMORY ERROR 	Not enough memory for operation
7 	USER ERROR 	Command line option error
6 	OPEN ERROR 	Open file error
5 	WRITE ERROR 	Write to disk error
4 	LOCKED ARCHIVE 	Attempt to modify an archive previously locked by the 'k' command
3 	CRC ERROR 	A CRC error occurred when unpacking
2 	FATAL ERROR 	A fatal error occurred
1 	WARNING 	Non fatal error(s) occurred
0 	SUCCESS 	Successful operation (User exit)"""
