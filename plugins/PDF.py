from __future__ import unicode_literals
import warnings
from plug import Filetypes

from PyPDF2 import PdfFileReader
from PyPDF2.utils import PdfReadWarning

@Filetypes.plugin(["pdf"])
class PDF(object):
    def __init__(self):
        pass

    def validate(self, path, ext):
        try:
            with open(path, "rb") as fr:
                with warnings.catch_warnings(record=True, module=PdfReadWarning) as w:
                    pdf = PdfFileReader(fr, strict=True)
                    pdf.getDocumentInfo()
                    for p in pdf.pages:
                        pass
                    if w:
                        return (1, str(w))

            return (0, "")
        except AssertionError as e:
            return (1, str(e))
        except Exception as e:
            return (1, str(e))
