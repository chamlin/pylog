import os
import re
import json

class mllog:

    def __init__(self, node, path, type='none'):
        self.node = node
        self.path = path
        # type (file, dir; error, request, access, unknown, none)
        self.type = type

    def __str__(self):
        return f"file: {self.path} (type {self.type})"

class mllogs:

    def __init__(self, config):
        self.config = config
        self.files = {}
        self.parse_file_config (config)
        self.detect_file_types ()

    def __str__(self):
        s = ""
        for key in self.files:
            s += f"{key}:\n"
            for file in self.files[key]:
                s += "    " + str (file) + "\n"
        return s

    def parse_file_config (self, config):
        # set up basic
        for node in self.config.keys():
            paths = self.config[node].split(',')
            for path in paths:
                path = path.strip()
                key = "'" + node + "' @ " + path
                # add then expand if needed
                log = mllog (node, path)
                if key in self.files:
                    self.files[key].append(log)
                else:
                    self.files[key] = [log]
                if os.path.isfile (path):
                    log.type = 'file'
                elif os.path.isdir (path):
                    log.type = 'dir'
                    # get the files and add them too
                    for root, dirs, files in os.walk(path):
                        for filename in files:
                            self.files[key].append (mllog (node, os.path.join(root, filename), 'file'))
    
    def detect_file_types(self):
        error_regex = re.compile ('\d\d\d\d-\d\d-\d\d \d\d:\d\d:\d\d\.\d+ (Finest|Finer|Fine|Debug|Config|Info|Notice|Warning|Error|Critical|Alert|Emergency): ')
        access_regex = re.compile ('\S+\s\S+\s\S+\s\[\d+/\w+/\d\d\d\d:\d\d:\d\d:\d\d.*HTTP')
        
        for key in self.files.keys():
            for file in self.files[key]:
                # print ('> ' + str(file))
                if file.type != 'file': continue
                with open(file.path, 'r', encoding='UTF-8') as afile:
                    lines = 0
                    while (line := afile.readline().rstrip()):
                        if lines > 5:
                            break
                        elif error_regex.match(line):
                            file.type = 'error'
                            break
                        elif access_regex.match(line):
                            file.type = 'access'
                            break
                        else:
                            try:
                                s = json.loads (line)
                                if 'time' in s: file.type = 'request'
                                break
                            except Exception:
                                pass
                        lines += 1
                # print ('< ' + str(file))



