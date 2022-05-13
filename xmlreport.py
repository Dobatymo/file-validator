from typing import Dict, Tuple
from xml.etree import ElementTree
from xml.sax.saxutils import XMLGenerator
from xml.sax.xmlreader import AttributesNSImpl


def load_report(path: str) -> Dict[str, Tuple[int, str]]:

    ret = dict()

    for event, elem in ElementTree.iterparse(path, events=["start"]):
        if elem.tag == "file":
            path = elem.attrib["path"]
            code = int(elem.attrib["code"])
            message = elem.text
            elem.clear()

            ret[path] = (code, message)

    return ret


class XmlReport:
    def __init__(self, filename: str, xslfile: str) -> None:

        self.fp = open(filename, "w", encoding="utf-8")
        self.xmlgen = XMLGenerator(self.fp)
        self.xmlgen.startDocument()
        self.xmlgen.processingInstruction("xml-stylesheet", f'type="text/xsl" href="{xslfile}"')
        attrs = AttributesNSImpl({}, {})
        self.xmlgen.startElementNS((None, "report"), "report", attrs)
        self.xmlgen.characters("\n")

    def __enter__(self):
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
