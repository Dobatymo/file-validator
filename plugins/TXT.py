from plug import Filetypes

@Filetypes.plugin(["txt"])
class TXT(object):
    def __init__(self):
        pass
    
    def validate(self, path, ext):
        return (0, "")
