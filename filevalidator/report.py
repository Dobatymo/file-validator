import logging
import os
from contextlib import ExitStack
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple
from xml.sax.saxutils import quoteattr

from genutility.json import json_lines
from lxml import etree
from typing_extensions import Self

logger = logging.getLogger(__name__)

XML_TEXT_NODE_LIMIT = 10_000_000
MAX_XML_MESSAGE_BYTES = XML_TEXT_NODE_LIMIT - 1
TRUNCATION_MARKER = " ,,, "
BACKSLASH_ENCODING = "backslash-xml10"


@dataclass(frozen=True)
class ReportEntry:
    code: int
    message: str
    size: int
    mtime_ns: Optional[int] = None


class ReportData(dict):
    def __init__(self, base: Optional[str] = None) -> None:
        super().__init__()
        self.base = base


class ReportBase:
    def __enter__(self) -> Self:
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def write(self, path: str, entry: ReportEntry) -> None:
        raise NotImplementedError

    def flush(self) -> None:
        raise NotImplementedError

    def close(self) -> None:
        raise NotImplementedError

    @staticmethod
    def load_report(path: Path, fail_on_dups: bool = True) -> ReportData:
        raise NotImplementedError


class Stdout(ReportBase):
    def flush(self) -> None:
        pass

    def close(self) -> None:
        pass

    def write(self, path: str, entry: ReportEntry) -> None:
        print(path, entry.code, entry.size, entry.mtime_ns, entry.message[:100].replace("\n", "\t"))


def _is_valid_xml10_codepoint(codepoint: int) -> bool:
    return (
        codepoint in (0x09, 0x0A, 0x0D)
        or 0x20 <= codepoint <= 0xD7FF
        or 0xE000 <= codepoint <= 0xFFFD
        or 0x10000 <= codepoint <= 0x10FFFF
    )


def _xml10_safe_text(value: str) -> str:
    """
    Replace characters that cannot be represented in XML 1.0 with
    visible Python-style escape sequences.

    Valid Unicode text is preserved unchanged.
    """
    parts: List[str] = []

    for char in value:
        codepoint = ord(char)

        if _is_valid_xml10_codepoint(codepoint):
            parts.append(char)
            continue

        if codepoint <= 0xFF:
            parts.append(f"\\x{codepoint:02x}")
        elif codepoint <= 0xFFFF:
            parts.append(f"\\u{codepoint:04x}")
        else:
            parts.append(f"\\U{codepoint:08x}")

    return "".join(parts)


def _encode_xml10_text(value: str) -> Tuple[str, str]:
    if all(_is_valid_xml10_codepoint(ord(char)) for char in value):
        return value, ""

    parts: List[str] = []
    for char in value:
        codepoint = ord(char)
        if char == "\\":
            parts.append("\\\\")
        elif _is_valid_xml10_codepoint(codepoint):
            parts.append(char)
        elif codepoint <= 0xFF:
            parts.append(f"\\x{codepoint:02x}")
        elif codepoint <= 0xFFFF:
            parts.append(f"\\u{codepoint:04x}")
        else:
            parts.append(f"\\U{codepoint:08x}")

    return "".join(parts), BACKSLASH_ENCODING


def _decode_xml10_text(value: str, encoding: str) -> str:
    if not encoding:
        return value
    if encoding != BACKSLASH_ENCODING:
        raise ValueError(f"Unsupported XML report text encoding: {encoding}")

    parts: List[str] = []
    i = 0
    escape_lengths = {"x": 2, "u": 4, "U": 8}

    while i < len(value):
        char = value[i]
        if char != "\\":
            parts.append(char)
            i += 1
            continue

        if i + 1 >= len(value):
            raise ValueError("Invalid trailing backslash in encoded XML report text")

        escape_type = value[i + 1]
        if escape_type == "\\":
            parts.append("\\")
            i += 2
            continue

        try:
            length = escape_lengths[escape_type]
        except KeyError:
            raise ValueError(f"Invalid escape sequence in encoded XML report text: \\{escape_type}") from None

        end = i + 2 + length
        digits = value[i + 2 : end]
        if len(digits) != length:
            raise ValueError("Truncated escape sequence in encoded XML report text")
        try:
            parts.append(chr(int(digits, 16)))
        except ValueError:
            raise ValueError(f"Invalid escape sequence in encoded XML report text: \\{escape_type}{digits}") from None
        i = end

    return "".join(parts)


def _decode_utf8_prefix(data: bytes, errors: str) -> str:
    while data:
        try:
            return data.decode("utf-8", errors=errors)
        except UnicodeDecodeError as e:
            data = data[: e.start]
    return ""


def _decode_utf8_suffix(data: bytes, errors: str) -> str:
    start = 0
    while start < len(data) and data[start] & 0xC0 == 0x80:
        start += 1
    return data[start:].decode("utf-8", errors=errors)


def _truncate_utf8(message: str, max_bytes: int, errors: str) -> str:
    data = message.encode("utf-8", errors=errors)
    marker_size = len(TRUNCATION_MARKER.encode("utf-8"))
    if marker_size > max_bytes:
        raise ValueError("XML message byte limit is too small for the truncation marker")

    available = max_bytes - marker_size
    beginning_bytes = (available + 1) // 2
    end_bytes = available // 2
    beginning = _decode_utf8_prefix(data[:beginning_bytes], errors)
    end = _decode_utf8_suffix(data[-end_bytes:], errors) if end_bytes else ""
    return beginning + TRUNCATION_MARKER + end


def _truncate_xml_message(message: str, max_bytes: int = MAX_XML_MESSAGE_BYTES) -> str:
    encoded, encoding = _encode_xml10_text(message)
    if len(encoded.encode("utf-8")) <= max_bytes:
        return message

    if not encoding:
        return _truncate_utf8(message, max_bytes, errors="strict")

    candidate_limit = max_bytes
    while True:
        candidate = _truncate_utf8(message, candidate_limit, errors="surrogatepass")
        encoded_candidate, _candidate_encoding = _encode_xml10_text(candidate)
        encoded_size = len(encoded_candidate.encode("utf-8"))
        if encoded_size <= max_bytes:
            return candidate

        scaled_limit = candidate_limit * max_bytes // encoded_size
        marker_size = len(TRUNCATION_MARKER.encode("utf-8"))
        candidate_limit = max(marker_size, min(candidate_limit - 1, scaled_limit))


class XmlReport(ReportBase):
    def __init__(self, path: Path, xslfile: str, base: Optional[str] = None) -> None:
        self._stack = ExitStack()
        self._closed = False

        try:
            self.xml = self._stack.enter_context(etree.xmlfile(os.fspath(path), encoding="utf-8"))

            self.xml.write_declaration()

            safe_xslfile = _xml10_safe_text(xslfile)

            pi = etree.ProcessingInstruction(
                "xml-stylesheet",
                f'type="text/xsl" href={quoteattr(safe_xslfile)}',
            )
            pi.tail = "\n"
            self.xml.write(pi)

            report_attrib = {}
            if base is not None:
                encoded_base, base_encoding = _encode_xml10_text(base)
                report_attrib["base"] = encoded_base
                if base_encoding:
                    report_attrib["base-encoding"] = base_encoding

            self._stack.enter_context(self.xml.element("report", report_attrib))
            self.xml.write("\n")

        except BaseException:
            self._stack.close()
            raise

    def write(self, path: str, entry: ReportEntry) -> None:
        if self._closed:
            raise RuntimeError("Cannot write to a closed XML report")

        encoded_path, path_encoding = _encode_xml10_text(path)
        truncated_message = _truncate_xml_message(entry.message)
        encoded_message, message_encoding = _encode_xml10_text(truncated_message)

        if path_encoding:
            logger.warning("Path contains characters invalid in XML 1.0; storing it with reversible escapes: %r", path)
        if truncated_message != entry.message:
            logger.warning("Truncated XML report message for %r to fit the XML text-node limit", path)

        elem = etree.Element("file", code=str(entry.code), path=encoded_path)
        elem.set("size", str(entry.size))
        if entry.mtime_ns is not None:
            elem.set("mtime_ns", str(entry.mtime_ns))
        if path_encoding:
            elem.set("path-encoding", path_encoding)
        if message_encoding:
            elem.set("message-encoding", message_encoding)
        elem.text = encoded_message

        self.xml.write(elem)
        self.xml.write("\n")

    def flush(self) -> None:
        if not self._closed:
            self.xml.flush()

    def close(self) -> None:
        if self._closed:
            return

        self._closed = True
        self._stack.close()

    @staticmethod
    def load_report(path: Path, fail_on_dups: bool = True) -> ReportData:
        ret = ReportData()

        for event, elem in etree.iterparse(
            os.fspath(path),
            events=("start", "end"),
            resolve_entities=False,
            no_network=True,
        ):
            if event == "start" and elem.tag == "report":
                if "base" in elem.attrib:
                    ret.base = _decode_xml10_text(elem.attrib["base"], elem.attrib.get("base-encoding", ""))
                continue
            if event != "end" or elem.tag != "file":
                continue

            filepath = _decode_xml10_text(elem.attrib["path"], elem.attrib.get("path-encoding", ""))
            code = int(elem.attrib["code"])
            message = _decode_xml10_text(elem.text or "", elem.attrib.get("message-encoding", ""))
            try:
                size = int(elem.attrib["size"])
            except KeyError:
                raise ValueError(f"Report entry does not contain the file size: {filepath}") from None
            mtime_ns = int(elem.attrib["mtime_ns"]) if "mtime_ns" in elem.attrib else None

            if fail_on_dups and filepath in ret:
                raise ValueError(f"Duplicate path found: {filepath}")

            ret[filepath] = ReportEntry(code, message, size, mtime_ns)

            # Keep memory usage bounded when loading a large report.
            elem.clear(keep_tail=True)

            parent = elem.getparent()
            if parent is not None:
                while elem.getprevious() is not None:
                    del parent[0]

        return ret


class JsonReport(ReportBase):
    def __init__(self, path: Path) -> None:
        self.jl = json_lines.from_path(path, "wt", encoding="utf-8")

    def write(self, path: str, entry: ReportEntry) -> None:
        self.jl.write(
            {
                "path": path,
                "code": entry.code,
                "message": entry.message,
                "size": entry.size,
                "mtime_ns": entry.mtime_ns,
            }
        )

    def flush(self) -> None:
        self.jl.flush()

    def close(self) -> None:
        self.jl.close()

    @staticmethod
    def load_report(path: Path, fail_on_dups: bool = True) -> ReportData:
        ret = ReportData()

        for obj in json_lines.from_path(path, "rt", encoding="utf-8"):
            filepath = obj["path"]

            if fail_on_dups and filepath in ret:
                raise ValueError(f"Duplicate path found: {filepath}")
            try:
                size = int(obj["size"])
            except KeyError:
                raise ValueError(f"Report entry does not contain the file size: {filepath}") from None
            except (TypeError, ValueError):
                raise ValueError(f"Report entry has an invalid file size: {filepath}") from None

            ret[filepath] = ReportEntry(obj["code"], obj["message"], size, obj.get("mtime_ns"))

        return ret


def load_report(path: Path) -> ReportData:
    if path.suffix == ".xml":
        return XmlReport.load_report(path)
    elif path.suffix in (".json", ".jl", ".jsonlines"):
        return JsonReport.load_report(path)
    else:
        raise ValueError(f"Unsupported file type: {path.suffix}")
