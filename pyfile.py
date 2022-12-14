import os
import re
import json
import sys

class mllog:

    def __init__(self, node, path, type='none'):
        self.node = node
        self.path = path
        # type (file, dir; error, request, access, unknown, none)
        self.type = type
        self.lines_read = 0
        self.lines_bad = 0

    def __str__(self):
        if self.lines_read == 0:
            return f"file: {self.path} (type {self.type})"
        else:
            return f"file: {self.path} (type {self.type}) {self.lines_bad}/{self.lines_read} lines bad"

class mllogs:

    def __init__(self, config):
        self.config = config
        self.files = {}
        self.data = []
        self.columns = {}
        # do some init stuff
        self.column_order = self.init_leading_columns(['time', 'node'])
        print (self.column_order)
        # do some stuff
        self.parse_file_config (config)
        self.detect_file_types ()
        self.read_files ()

    def __str__(self):
        s = ""
        for key in self.files:
            s += f"{key}:\n"
            for file in self.files[key]:
                s += "    " + str (file) + "\n"
        return s

    def init_leading_columns (self, order):
        column_ratings = {}
        for num, name in [[col, order[col]] for col in range(len(order))]:
            column_ratings[name] = f"!{num:04d}"
        return lambda colname: column_ratings.get(colname, colname)

    def parse_file_config (self, config):
        # set up basic
        for node, config_path in self.config.items():
            paths = config_path.split(',')
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
        
        for key, files in self.files.items():
            for file in files:
                if file.type != 'file': continue
                with open(file.path, 'r', encoding='UTF-8') as afile:
                    lines = 0
                    try:
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
                    except Exception:
                        print (f"Bad read in {file.path}, can't determine type.", file=sys.stderr, flush=True)

    def read_files(self):
        print ("Reading files", file=sys.stderr, flush=True)
        for key, files in self.files.items():
            for file in files:
                if file.type != 'request': continue
                print ("- " + file.path, file=sys.stderr, flush=True)
                with open(file.path, 'r', encoding='UTF-8') as afile:
                    lines_read, lines_bad = [0, 0]
                    while (line := afile.readline().rstrip()):
                        lines_read += 1
                        try:
                            s = json.loads (line)
                            s['node'] = file.node
                            self.columns.update(s)   
                            self.data.append(s)
                        except Exception:
                            lines_bad += 1
                            print(f"Bad line from {file.path}: " + line,  file=sys.stderr)
                file.lines_read = lines_read
                file.lines_bad = lines_bad
        # just keep the keys
        self.columns = sorted(self.columns.keys(), key=self.column_order)

    def dump_data(self):
        columns = self.columns
        # header
        print ('\t'.join (columns))
        for row in self.data:
            print ('\t'.join([str(row.get(col,'')) for col in columns]))

