
class mllog:

    def __init__(self, node, path):
        self.node = node
        self.path = path

class mllogs:

    species = "Canis familiaris"

    def __init__(self, config):
        self.config = config
        self.files = {}

    def __str__(self):
        s = ""
        for key in self.files:
            s += f"node = {key}:\n"
            for file in self.files[key]:
                s += f"    {file.node} @ {file.path}\n"
        return s

    def check_config (self):
        for node in self.config.keys():
            paths = self.config[node].split(',')
            print (paths)
            for path in paths:
                print (f"{node} @ {path}")
                print (node in self.files)
                if node in self.files:
                    self.files[node].append(mllog (node, path.strip()))
                else:
                    self.files[node] = [mllog (node, path.strip())]
        print(self.files)
