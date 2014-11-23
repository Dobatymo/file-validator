from __future__ import unicode_literals
from plug import Filetypes

from pyPdf import PdfFileReader

@Filetypes.plugin(["pdf"])
class PDF(object):
    def __init__(self):
        pass
    
    def validate(self, path, ext):
        try:
            with open(path, "rb") as fr:
                pdf = PdfFileReader(fr)
                pdf.getDocumentInfo()
                for p in pdf.pages:
                    pass
            return (0, "")
        except AssertionError as e:
            return (1, str(e))
        except Exception as e:
            return (1, str(e))
