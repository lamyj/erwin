import spire

class MeanResponse(spire.TaskFactory):
    def __init__(self, sources, target):
        spire.TaskFactory.__init__(self, str(target))
        
        self.file_dep = sources
        self.targets = [target]
        
        self.actions = [["responsemean", "-force"] + sources + [target]]

def main():
    return entrypoint(
        MeanResponse, [
            ("sources", {"nargs": "+", "help": "Source responses"}),
            ("target", {"help": "Target average response"})
        ])
