import logging
import warnings
from shutil import which
from typing import Dict, Optional

from pypdf import PdfReader

from ..limits import (
    DEFAULT_MAX_FILE_SIZE,
    CommandError,
    CommandTimeout,
    check_file_size,
    run_command,
    timeout_result,
)
from ..plug import Filetypes, ValidationResult

logger = logging.getLogger(__name__)


@Filetypes.plugin(["pdf"])
class PDF:
    def __init__(
        self,
        max_file_size: Optional[int] = DEFAULT_MAX_FILE_SIZE,
        max_file_size_by_extension: Optional[Dict[str, Optional[int]]] = None,
        qpdf_binary: Optional[str] = None,
        timeout: Optional[float] = 3600,
    ) -> None:
        qpdf_binary = qpdf_binary or "qpdf"
        self.qpdf_binary = which(qpdf_binary)
        if self.qpdf_binary is None:
            logger.info("qpdf executable %r not found; falling back to pypdf validation", qpdf_binary)
        self.timeout = timeout
        self.max_file_size = max_file_size
        self.max_file_size_by_extension = max_file_size_by_extension

    @staticmethod
    def _validate_pypdf(path: str, strict: bool) -> ValidationResult:
        try:
            with open(path, "rb") as fr:
                with warnings.catch_warnings(record=strict) as ws:
                    warnings.simplefilter("always")
                    pdf = PdfReader(fr, strict=True)
                    pdf.metadata  # noqa: B018
                    for _p in pdf.pages:
                        pass
                    if ws:
                        return (1, "\n".join(str(w.message) for w in ws))

            return (0, "")
        except OSError:
            raise
        except AssertionError as e:
            return (1, str(e))
        except Exception as e:
            return (1, str(e))

    def validate(self, path: str, ext: str, file_size: int, strict: bool = True) -> ValidationResult:
        size_result = check_file_size(file_size, ext, self.max_file_size, self.max_file_size_by_extension)
        if size_result:
            return size_result

        if self.qpdf_binary is not None:
            cmd = [self.qpdf_binary, "--check", path]
            try:
                run_command(cmd, self.timeout)
                return (0, "")
            except CommandError as e:
                if e.returncode == 3 and not strict:
                    return (0, "")
                if e.returncode in {2, 3}:
                    return (1, e.output or f"qpdf failed with error code {e.returncode}")
                return (-1, e.output or f"qpdf failed with unexpected error code {e.returncode}")
            except CommandTimeout as e:
                return timeout_result(cmd, self.timeout, e.output)

        return self._validate_pypdf(path, strict)
