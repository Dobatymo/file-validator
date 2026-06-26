import re

from ..plug import Filetypes, ValidationResult

PACK_START = b"\x00\x00\x01\xba"
PRIVATE_STREAM_1 = b"\x00\x00\x01\xbd"

MAGIC = "# VobSub index file"

FIELD_PATTERNS = {
    "size": re.compile(r"\d+x\d+$"),
    "palette": re.compile(r"[0-9a-fA-F]{6}(?:,\s*[0-9a-fA-F]{6}){15}$"),
    "langidx": re.compile(r"\d+$"),
    "id": re.compile(r"[^,\s]+,\s*index:\s*\d+$"),
    "delay": re.compile(r"[-+]?\d{2}:\d{2}:\d{2}:\d{3}$"),
    "timestamp": re.compile(r"[-+]?\d{2}:\d{2}:\d{2}:\d{3},\s*filepos:\s*[0-9a-fA-F]+$"),
}

LOOSE_FIELDS = {
    "alpha",
    "align",
    "custom colors",
    "fadein/out",
    "forced subs",
    "org",
    "scale",
    "smooth",
    "time offset",
}


@Filetypes.plugin(["idx", "sub"])
class VobSub:
    def __init__(self) -> None:
        pass

    def validate(self, path: str, ext: str, file_size: int, strict: bool = True) -> ValidationResult:
        if ext == "idx":
            return self.validate_idx(path)
        return self.validate_sub(path, file_size)

    def validate_idx(self, path: str) -> ValidationResult:
        saw_magic = False
        saw_timestamp = False

        with open(path, encoding="latin1") as fr:
            for lineno, line in enumerate(fr, 1):
                stripped = line.strip()
                if not stripped:
                    continue
                if stripped == "\0":
                    continue
                if stripped.startswith("#"):
                    if lineno == 1 and stripped.startswith(MAGIC):
                        saw_magic = True
                    continue

                name, sep, value = stripped.partition(":")
                if not sep:
                    return (1, f"Line {lineno} is not a VobSub idx field: {stripped!r}")

                name = name.lower()
                value = value.strip()
                pattern = FIELD_PATTERNS.get(name)
                if pattern:
                    if pattern.fullmatch(value) is None:
                        return (1, f"Line {lineno} has invalid {name!r} value: {value!r}")
                    saw_timestamp = saw_timestamp or name == "timestamp"
                elif name not in LOOSE_FIELDS:
                    return (1, f"Line {lineno} has unknown VobSub idx field: {name!r}")

        if not saw_magic:
            return (1, "Missing VobSub idx header")
        if not saw_timestamp:
            return (1, "Missing VobSub timestamp entries")
        return (0, "")

    def validate_sub(self, path: str, file_size: int) -> ValidationResult:
        if file_size < len(PACK_START):
            return (1, "VobSub sub file is too small")

        with open(path, "rb") as fr:
            if fr.read(len(PACK_START)) != PACK_START:
                return (1, "VobSub sub file does not start with an MPEG pack header")

            offset = len(PACK_START)
            tail = b""
            while True:
                chunk = fr.read(65536)
                if not chunk:
                    break
                data = tail + chunk
                pos = data.find(PRIVATE_STREAM_1)
                if pos != -1:
                    packet_offset = offset - len(tail) + pos
                    fr.seek(packet_offset + len(PRIVATE_STREAM_1))
                    length = fr.read(2)
                    if len(length) != 2:
                        return (1, "Truncated MPEG private stream packet length")
                    packet_length = int.from_bytes(length, "big")
                    if packet_length == 0:
                        return (1, "Empty MPEG private stream subtitle packet")
                    if packet_offset + len(PRIVATE_STREAM_1) + 2 + packet_length > file_size:
                        return (1, "Truncated MPEG private stream subtitle packet")
                    return (0, "")
                tail = data[-3:]
                offset += len(chunk)

        return (1, "Missing MPEG private stream 1 subtitle packets")
