
class mllog:

    def __init__(self, node, path):
        self.node = node
        self.path = path
        # filename, type (error, request, access, unknown, none)
        self.file = {'filename': 'unknown', 'type': 'unknown'}

    def __str__(self):
        return f"{self.node} @ {self.path} -> {self.file['filename']} (type self.file['type'])"

class mllogs:

    def __init__(self, config):
        self.config = config
        self.files = {}
        self.parse_config (config)

    def __str__(self):
        s = ""
        for key in self.files:
            s += f"{key}:\n"
            for file in self.files[key]:
                s += str (file) + "\n"
        return s

    def parse_config (self, config):
        # set up basic
        for node in self.config.keys():
            paths = self.config[node].split(',')
            for path in paths:
                key = node + '@' + path
                if node in self.files:
                    self.files[key].append(mllog (node, path.strip()))
                else:
                    self.files[key] = [mllog (node, path.strip())]
        # now go through and get actual files
        
