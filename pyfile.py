import os

class mllog:

    def __init__(self, node, path):
        self.node = node
        self.path = path
        # filename, type (error, request, access, unknown, none)
        self.file = {'filename': path, 'type': 'none'}

    def __str__(self):
        return f"file: {self.file['filename']} (type {self.file['type']})"

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
                s += "    " + str (file) + "\n"
        return s

    def parse_config (self, config):
        # set up basic
        for node in self.config.keys():
            paths = self.config[node].split(',')
            for path in paths:
                path = path.strip()
                key = node + '@' + path
                if node in self.files:
                    self.files[key].append(mllog (node, path))
                else:
                    self.files[key] = [mllog (node, path)]
        # now go through and get actual files
        for key in self.files:
            print (f"checking {key}:\n")
            for log in self.files[key]:
                if os.path.isfile (log.file['filename']):
                    log.file['type'] = 'file'
                elif os.path.isdir (log.file['filename']):
                    log.file['type'] = 'dir'
        
