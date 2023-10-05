import logging
import os
import re
import subprocess
from pathlib import Path
from typing import Tuple

from genutility.fileformats.rar import Rar, RarError, force_decode  # use 'pip install rarfile' module instead ?
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

            p = Path(path)
            m = re.match(r"^(.*)\.part([0-9]+)\.(rar|cbr)$", p.name)
            if m:
                name, part, ext = m.groups()
                if int(part) != 1:
                    filename = f"{name}.part{(len(part)-1)*'0'}1.{ext}"
                    part_one = p.parent / filename
                    if part_one.is_file():
                        return (-2, "Skipping multi-part archive")
                    else:
                        return (1, "Multi-part archive missing initial part")

            r = Rar(p, executable)
            try:
                r.test()
                return (0, "")
            except RarError as e:
                return (1, f"Calling {executable} failed with error code [{e.returncode}]: {e.output}")
            except Exception:
                logger.exception("Calling `%s` failed", executable)
                return (-1, f"Calling `{executable}` failed")
        elif ext in {"wim"}:
            # "C:\Program Files (x86)\Windows Kits\10\Tools\bin\i386\imagex.exe" /info "C:\Windows\Containers\WindowsDefenderApplicationGuard.wim" /check
            foundexe = False
        else:
            foundexe = False

        if foundexe:
            try:
                cmd = f'"{executable}" {args} "{path}"'
                subprocess.check_output(cmd, stderr=subprocess.STDOUT, cwd=os.getcwd())  # nosec
                return (0, "")
            except subprocess.CalledProcessError as e:
                output = force_decode(e.output).strip()
                return (1, f"Calling {executable} failed with error code [{e.returncode}]: {output}")
            except Exception:
                logger.exception("Calling `%s` failed", cmd)
                return (-1, f"Calling `{cmd}` failed")

        raise RuntimeError("Could not find archiver executable")
