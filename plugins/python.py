from __future__ import absolute_import, division, print_function, unicode_literals

from plug import Filetypes

@Filetypes.plugin(["py", "pyw"])
class Python(object):
    def __init__(self):
        pass
    
    def validate(self, path, ext):
        try:
            with open(path, "rb") as fr:
                compile(fr.read(), "<file>", "exec")
            return (0, "")
        except (SyntaxError, TypeError) as e:
            return (1, str(e))
