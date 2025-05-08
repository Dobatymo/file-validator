import logging
import os
import re
import subprocess
from pathlib import Path
from shutil import which
from typing import Tuple

from genutility.fileformats.rar import Rar, RarError, force_decode  # use 'pip install rarfile' module instead ?
from genutility.filesystem import fileextensions

from ..plug import Filetypes, PluginError

logger = logging.getLogger(__name__)

extensions = set(fileextensions.archives + fileextensions.image_archives + fileextensions.compressed) - {
    "zip",
    "cbz",
}  # zip handled by zip.py


@Filetypes.plugin(extensions)
class Archives:
    def __init__(self, unrar_binary: str = "rar", sevenzip_binary: str = "7z") -> None:
        _unrar_binary = which(unrar_binary)

        if _unrar_binary is None:
            self.unrar_binary = None
        else:
            self.unrar_binary = Path(_unrar_binary)

        _sevenzip_binary = which(sevenzip_binary)
        if _sevenzip_binary is None:
            self.sevenzip_binary = None
        else:
            self.sevenzip_binary = Path(_sevenzip_binary)

        if self.unrar_binary is None and self.sevenzip_binary is None:
            raise PluginError("Unrar and 7z binaries not found")

    def validate(self, path: str, ext: str, strict: bool = True) -> Tuple[int, str]:
        foundexe = True
        if (
            ext
            in (
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
            )
            and self.sevenzip_binary is not None
        ):
            executable = self.sevenzip_binary
            args = ["t", "-p-"]
        elif ext in ("rar", "cbr") and self.unrar_binary is not None:
            executable = self.unrar_binary
            # args = "t -p-"
            foundexe = False

            p = Path(path)
            m = re.match(r"^(.*)\.part([0-9]+)\.(rar|cbr)$", p.name)
            if m:
                name, part, ext = m.groups()
                if int(part) != 1:
                    filename = f"{name}.part{(len(part) - 1) * '0'}1.{ext}"
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
            cmd = [os.fspath(executable), *args, path]
            try:
                subprocess.check_output(cmd, stderr=subprocess.STDOUT, cwd=os.getcwd())  # nosec
                return (0, "")
            except subprocess.CalledProcessError as e:
                output = force_decode(e.output).strip()
                return (1, f"Calling {executable} failed with error code [{e.returncode}]: {output}")
            except Exception:
                logger.exception("Calling `%s` failed", cmd)
                return (-1, f"Calling `{cmd}` failed")

        raise PluginError("Could not find archiver binary executable")
