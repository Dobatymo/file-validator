from __future__ import unicode_literals
import warnings
from plug import Filetypes

from PyPDF2 import PdfFileReader

@Filetypes.plugin(["pdf"])
class PDF(object):

    def __init__(self):
        pass

    def validate(self, path, ext, strict=True):
        # type: (str, str, bool) -> Tuple[bool, str]

        try:
            with open(path, "rb") as fr:
                with warnings.catch_warnings(record=strict) as ws:
                    pdf = PdfFileReader(fr, strict=True, overwriteWarnings=False)
                    pdf.getDocumentInfo()
                    for p in pdf.pages:
                        pass
                    if ws:
                        return (1, "\n".join(str(w.message) for w in ws))

            return (0, "")
        except AssertionError as e:
            return (1, str(e))
        except Exception as e:
            return (1, str(e))
