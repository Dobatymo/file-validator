import subprocess
from typing import Dict, List, Optional

from genutility.subprocess import force_decode

from .plug import ValidationResult

DEFAULT_MAX_FILE_SIZE = 1024**3


class CommandError(Exception):
    def __init__(self, returncode: int, cmd: List[str], output: str) -> None:
        self.returncode = returncode
        self.cmd = cmd
        self.output = output
        super().__init__(f"Calling {cmd} failed with error code [{returncode}]: {output}")


class CommandTimeout(Exception):
    def __init__(self, cmd: List[str], timeout: Optional[float], output: str) -> None:
        self.cmd = cmd
        self.timeout = timeout
        self.output = output
        super().__init__(f"Timed out after {timeout} seconds: {cmd}")


def check_file_size(
    file_size: int,
    ext: str,
    max_file_size: Optional[int],
    max_file_size_by_extension: Optional[Dict[str, Optional[int]]] = None,
) -> Optional[ValidationResult]:
    limit = max_file_size
    if max_file_size_by_extension:
        limit = max_file_size_by_extension.get(ext, limit)

    if limit is None:
        return None

    if file_size > limit:
        return (-1, f"File too large to validate: {file_size} bytes > {limit} bytes")

    return None


def has_os_error_errno(error: OSError) -> bool:
    return error.errno is not None


def run_command(cmd: List[str], timeout: Optional[float], cwd: Optional[str] = None) -> str:
    try:
        result = subprocess.run(
            cmd,
            check=True,
            cwd=cwd,
            stderr=subprocess.STDOUT,
            stdout=subprocess.PIPE,
            timeout=timeout,
        )
    except subprocess.CalledProcessError as e:
        output = force_decode(e.output or b"").strip()
        raise CommandError(e.returncode, e.cmd, output) from e
    except subprocess.TimeoutExpired as e:
        output = force_decode(e.output or b"").strip()
        raise CommandTimeout(e.cmd, e.timeout, output) from e

    return force_decode(result.stdout or b"").strip()


def timeout_result(cmd: List[str], timeout: Optional[float], output: str = "") -> ValidationResult:
    message = f"Timed out after {timeout} seconds: {cmd}"
    if output:
        message += f": {output}"
    return (-1, message)
