import logging
import os
import re
from pathlib import Path
from shutil import which
from typing import Optional

from genutility.fileformats.rar import Rar, RarError  # use 'pip install rarfile' module instead ?
from genutility.filesystem import fileextensions

from ..limits import CommandError, CommandTimeout, run_command, timeout_result
from ..plug import Filetypes, PluginError, ValidationResult

logger = logging.getLogger(__name__)

extensions = set(fileextensions.archives + fileextensions.image_archives + fileextensions.compressed) - {
    "zip",
    "cbz",
}  # zip handled by zip.py


@Filetypes.plugin(extensions)
class Archives:
    def __init__(
        self, unrar_binary: str = "rar", sevenzip_binary: str = "7z", timeout: Optional[float] = 86400
    ) -> None:
        self.timeout = timeout
        self.unrar_binary_config = unrar_binary
        self.sevenzip_binary_config = sevenzip_binary
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
            raise PluginError(
                "Archive validator cannot start because neither configured executable was found: "
                f"unrar_binary={unrar_binary!r}, sevenzip_binary={sevenzip_binary!r}"
            )

    def validate(self, path: str, ext: str, file_size: int, strict: bool = True) -> ValidationResult:
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
            except OSError:
                raise
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
                run_command(cmd, self.timeout, cwd=os.getcwd())
                return (0, "")
            except CommandError as e:
                return (1, f"Calling {executable} failed with error code [{e.returncode}]: {e.output}")
            except CommandTimeout as e:
                return timeout_result(cmd, self.timeout, e.output)
            except OSError:
                raise
            except Exception:
                logger.exception("Calling `%s` failed", cmd)
                return (-1, f"Calling `{cmd}` failed")

        if ext in {"cb7", "cbt", "cba", "7z", "gz", "bz2", "xz", "z", "lzma", "tar", "tgz", "tbz", "cab"}:
            raise PluginError(
                f"Cannot validate extension {ext!r}: configured 7z executable "
                f"{self.sevenzip_binary_config!r} was not found"
            )
        if ext in {"rar", "cbr"}:
            raise PluginError(
                f"Cannot validate extension {ext!r}: configured RAR executable "
                f"{self.unrar_binary_config!r} was not found"
            )
        if ext == "wim":
            raise PluginError("Cannot validate extension 'wim': WIM validation is not implemented")
        raise PluginError(
            f"Cannot validate extension {ext!r}: the archive plugin registers it but has no validation implementation"
        )
