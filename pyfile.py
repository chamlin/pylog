import os

class mllog:

    def __init__(self, node, path, type='none'):
        self.node = node
        self.path = path
        # filename, type (error, request, access, unknown, none)
        self.file = {'filename': path, 'type': type}

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
                # add then expand if needed
                log = mllog (node, path)
                if key in self.files:
                    self.files[key].append(log)
                else:
                    self.files[key] = [log]
                if os.path.isfile (path):
                    log.file['type'] = 'file'
                elif os.path.isdir (path):
                    log.file['type'] = 'dir'
                    # get the files and add them too
                    for root, dirs, files in os.walk(path):
                        for filename in files:
                            self.files[key].append (mllog (node, filename, 'file'))
        
