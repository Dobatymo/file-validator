from typing import Dict, Tuple
from xml.etree import ElementTree
from xml.sax.saxutils import XMLGenerator
from xml.sax.xmlreader import AttributesNSImpl


def load_report(path: str, fail_on_dups: bool = True) -> Dict[str, Tuple[int, str]]:
    ret: Dict[str, Tuple[int, str]] = {}

    for event, elem in ElementTree.iterparse(path, events=["start"]):
        if elem.tag == "file":
            path = elem.attrib["path"]
            code = int(elem.attrib["code"])
            message = elem.text or ""
            elem.clear()

            if fail_on_dups and path in ret:
                raise ValueError(f"Duplicate path found: {path}")
            ret[path] = (code, message)

    return ret


class XmlReport:
    def __init__(self, filename: str, xslfile: str) -> None:
        self.fp = open(filename, "w", encoding="utf-8")
        self.xmlgen = XMLGenerator(self.fp, encoding="utf-8")
        self.xmlgen.startDocument()
        self.xmlgen.processingInstruction("xml-stylesheet", f'type="text/xsl" href="{xslfile}"')
        attrs = AttributesNSImpl({}, {})
        self.xmlgen.characters("\n")
        self.xmlgen.startElementNS((None, "report"), "report", attrs)
        self.xmlgen.characters("\n")

    def __enter__(self) -> "XmlReport":
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

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
