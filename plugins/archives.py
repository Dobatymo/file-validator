import logging
import subprocess
import sys
from pathlib import Path
from typing import Tuple

from genutility.fileformats.rar import Rar, RarError  # use 'pip install rarfile' module instead ?
from genutility.filesystem import fileextensions

from plug import Filetypes

logger = logging.getLogger(__name__)

extensions = set(fileextensions.archives + fileextensions.image_archives + fileextensions.compressed) - {
    "zip",
    "cbz",
}  # zip handled by zip.py


@Filetypes.plugin(extensions)
class Archives:
    def __init__(self, UnRarExecutable: str, SevenZipExecutable: str) -> None:

        self.UnRarExecutable = Path(UnRarExecutable)
        self.SevenZipExecutable = Path(SevenZipExecutable)

    def validate(self, path: str, ext: str) -> Tuple[int, str]:

        foundexe = True
        if ext in (
            "cb7",
            "cbt",
            "cba",
            "7z",
            "gz",
            "bz2",
            "xz",
            "z",
            "lzma",
            "tar",
            "tgz",
            "tbz",
            "cab",
        ):
            executable = self.SevenZipExecutable
            args = "t -p-"
        elif ext in ("rar", "cbr"):
            executable = self.UnRarExecutable
            # args = u"t -p-"
            foundexe = False
            r = Rar(Path(path), executable)
            try:
                r.test()
                return (0, "")
            except RarError as e:
                return (1, f"{str(e)} [{e.cmd}] [{e.returncode}]: {e.output}")
        elif ext in {"wim"}:
            # "C:\Program Files (x86)\Windows Kits\10\Tools\bin\i386\imagex.exe" /info "C:\Windows\Containers\WindowsDefenderApplicationGuard.wim" /check
            foundexe = False
        else:
            foundexe = False

        if foundexe:
            try:
                cmd = f'"{executable}" {args} "{path}"'
                subprocess.check_output(cmd)
                return (0, "")
            except UnicodeEncodeError:
                logger.error("UnicodeEncodeError for %s", path)
                raise
            except subprocess.CalledProcessError as e:
                try:
                    output = e.output.decode(sys.stdout.encoding).replace("\n\n", "\n")
                    return (1, f"{str(e)} [{e.cmd}] [{e.returncode}]: {output}")
                except UnicodeDecodeError:
                    logger.exception(path)
                    raise

        raise RuntimeError("Could not find archiver executable")
