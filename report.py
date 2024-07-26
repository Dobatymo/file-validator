from pathlib import Path
from typing import Dict, Tuple
from xml.etree import ElementTree  # nosec
from xml.sax.saxutils import XMLGenerator  # nosec
from xml.sax.xmlreader import AttributesNSImpl  # nosec

from genutility.json import json_lines
from typing_extensions import Self


def load_report(path: str, fail_on_dups: bool = True) -> Dict[str, Tuple[int, str]]:
    ret: Dict[str, Tuple[int, str]] = {}

    for _event, elem in ElementTree.iterparse(path, events=["start"]):  # nosec
        if elem.tag == "file":
            path = elem.attrib["path"]
            code = int(elem.attrib["code"])
            message = elem.text or ""
            elem.clear()

            if fail_on_dups and path in ret:
                raise ValueError(f"Duplicate path found: {path}")
            ret[path] = (code, message)

    return ret


class ReportBase:
    def __enter__(self) -> Self:
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def write(self, path: str, code: str, message: str) -> None:
        raise NotImplementedError

    def flush(self) -> None:
        raise NotImplementedError

    def close(self) -> None:
        raise NotImplementedError


class Stdout(ReportBase):
    def flush(self) -> None:
        pass

    def close(self) -> None:
        pass

    def write(self, path: str, code: str, message: str) -> None:
        print(path, code, message[:100].replace("\n", "\t"))


class XmlReport(ReportBase):
    def __init__(self, path: Path, xslfile: str) -> None:
        self.fp = path.open("w", encoding="utf-8")
        self.xmlgen = XMLGenerator(self.fp, encoding="utf-8")
        self.xmlgen.startDocument()
        self.xmlgen.processingInstruction("xml-stylesheet", f'type="text/xsl" href="{xslfile}"')
        attrs = AttributesNSImpl({}, {})
        self.xmlgen.characters("\n")
        self.xmlgen.startElementNS((None, "report"), "report", attrs)
        self.xmlgen.characters("\n")

    def write(self, path: str, code: str, message: str) -> None:
        attr_vals = {("", "code"): code, ("", "path"): path}
        attr_qnames = {("", "code"): "code", ("", "path"): "path"}
        attrs = AttributesNSImpl(attr_vals, attr_qnames)
        self.xmlgen.startElementNS((None, "file"), "file", attrs)
        self.xmlgen.characters(message)
        self.xmlgen.endElementNS((None, "file"), "file")
        self.xmlgen.characters("\n")

    def flush(self) -> None:
        self.fp.flush()

    def close(self) -> None:
        self.xmlgen.endElementNS((None, "report"), "report")
        self.xmlgen.endDocument()
        self.fp.close()


class JsonReport(ReportBase):
    def __init__(self, path: Path) -> None:
        self.jl = json_lines.from_path(path, "wt", encoding="utf-8")

    def write(self, path: str, code: str, message: str) -> None:
        self.jl.write({"path": path, "code": code, "message": message})

    def flush(self) -> None:
        self.jl.flush()

    def close(self) -> None:
        self.jl.close()
