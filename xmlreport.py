from __future__ import absolute_import, division, print_function, unicode_literals

from io import open
from xml.sax.saxutils import XMLGenerator
from xml.sax.xmlreader import AttributesNSImpl

class xmlreport(object):

    def __init__(self, filename, xslfile):
        self.fp = open(filename, "wb")
        self.xmlgen = XMLGenerator(self.fp, "utf-8")
        self.xmlgen.startDocument()
        self.xmlgen.processingInstruction("xml-stylesheet", 'type="text/xsl" href="{}"'.format(xslfile))
        attrs = AttributesNSImpl({}, {})
        self.xmlgen.startElementNS((None, "report"), "report", attrs)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def write(self, path, code, message):
        attr_vals = {
            (None, "code"): code,
            (None, "path"): path
        }
        attr_qnames = {
            (None, "code"): "code",
            (None, "path"): "path"
        }
        attrs = AttributesNSImpl(attr_vals, attr_qnames)
        self.xmlgen.startElementNS((None, "file"), "file", attrs)
        self.xmlgen.characters(message)
        self.xmlgen.endElementNS((None, "file"), "file")

    def newline(self):
        #self.fp.write("\n")
        self.xmlgen.characters("\n")

    def flush(self):
        self.fp.flush()

    def close(self):
        self.xmlgen.endElementNS((None, "report"), "report")
        self.xmlgen.endDocument()
        self.fp.close()
