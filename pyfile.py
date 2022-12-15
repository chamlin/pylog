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
        self.months = {'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6, 'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12}

        # do some init stuff
        self.column_order = self.init_leading_columns(['time', 'node', '_ftype'])
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
                if file.type == 'request':
                    self.read_request_file (file)
                elif file.type == 'access':
                    self.read_access_file (file)
                elif file.type == 'error':
                    self.read_error_file (file)
        # just keep the keys
        self.columns = sorted(self.columns.keys(), key=self.column_order)

    def read_request_file (self, file):
        print ("- " + file.path, file=sys.stderr, flush=True)
        with open(file.path, 'r', encoding='UTF-8') as request_file:
            lines_read, lines_bad = [0, 0]
            while (line := request_file.readline().rstrip()):
                lines_read += 1
                try:
                    vals = json.loads (line)
                    vals['node'] = file.node
                    # TODO - genericize?
                    vals['_fname'] = file.path
                    vals['_ftype'] = file.type
                    self.columns.update(vals)   
                    self.data.append(vals)
                except Exception:
                    lines_bad += 1
                    print(f"Bad line from request file {file.path}: " + line,  file=sys.stderr)
        file.lines_read = lines_read
        file.lines_bad = lines_bad


    def read_access_file (self, file):
        access_regex = re.compile ('(\S+)\s(\S+)\s(\S+)\s\[(\d+)/(\w+)/(\d\d\d\d):(\d\d):(\d\d):(\d\d) ([^]]+)\] "(\w+) (\S+) (\S+)" (\d+) (\S+) (\S+) "([^"]+)"')
        access_columns = ('ip', 'thing', 'user', 'day', 'month', 'year', 'hour', 'minute', 'second', 'timezone', 'method', 'URL', 'protocol', 'response', 'bytes', 'referrer', 'client')

        print ("- " + file.path, file=sys.stderr, flush=True)
        with open(file.path, 'r', encoding='UTF-8') as request_file:
            lines_read, lines_bad = [0, 0]
            while (line := request_file.readline().rstrip()):
                lines_read += 1
                try:
                    m = access_regex.match(line)
                    # TODO - genericize?
                    # TODO - save timezone?
                    vals = {'_fname': file.path, '_ftype': file.type}
                    for index in range(len(access_columns)):
                        vals[access_columns[index]] = m.group(index+1)
                    vals['time'] = f"{int(vals['day']):02d}-{self.months[vals['month']]:02d}-{int(vals['year']):04d}"
                    vals['time'] += f" {int(vals['hour']):02d}:{int(vals['minute']):02d}:{int(vals['second']):02d}"
                    self.columns.update(vals)   
                    self.data.append(vals)
                except Exception as oops:
                    lines_bad += 1
                    print(f"Bad line from access file {file.path}: " + line,  file=sys.stderr)
                    print (oops)
        file.lines_read = lines_read
        file.lines_bad = lines_bad

    def read_error_filex (self, file):
        prefix_regex = re.compile ('(?P<time>\d\d\d\d-\d\d-\d\d \d\d:\d\d:\d\d\.\d+) (?P<level>\S+):\s(?P<rest>.*)')

        print ("- " + file.path, file=sys.stderr, flush=True)
        with open(file.path, 'r', encoding='UTF-8') as request_file:
            lines_read, lines_bad = [0, 0]
            while (line := request_file.readline().rstrip()):
                lines_read += 1
                try:
                    m = prefix_regex.match(line)
                    # TODO - genericize?
                    vals = {'_fname': file.path, '_ftype': file.type, 'time': m.group('time')}
                    self.columns.update(vals)   
                    self.data.append(vals)
                except Exception as oops:
                    lines_bad += 1
                    print(f"Bad line from access file {file.path}: " + line,  file=sys.stderr)
                    print (oops)
        file.lines_read = lines_read
        file.lines_bad = lines_bad

    def read_error_file (self, file):
        prefix_regex = re.compile ('(?P<time>\d\d\d\d-\d\d-\d\d \d\d:\d\d:\d\d\.\d+) (?P<level>\S+):\s(?P<rest>.*)')

        print ("- " + file.path, file=sys.stderr, flush=True)
        with open(file.path, 'r', encoding='UTF-8') as request_file:
            lines_read, lines_bad = [0, 0]
            while (line := request_file.readline().rstrip()):
                lines_read += 1
                rows_out = self.classify_error_line(file, line)
                if len(rows_out) > 0:
                    self.data += rows_out
                    [self.columns.update(row) for row in rows_out]
                else:
                    print(f"Bad line from access file {file.path}: " + line,  file=sys.stderr)
                    lines_bad += 1
        file.lines_read = lines_read
        file.lines_bad = lines_bad

    def classify_error_line (self, file, line):
        prefix_regex = re.compile ('(?P<time>\d\d\d\d-\d\d-\d\d \d\d:\d\d:\d\d\.\d+) (?P<level>\S+):\s(?P<rest>.*)')
        # return list of extracted rows.  0 means error or bad line, whatever
        retval = []

        try:
            m = prefix_regex.match(line)
            # TODO - genericize?
            vals = {'_fname': file.path, '_ftype': file.type, 'time': m.group('time'), 'node': file.node}
            retval.append(vals)
        except Exception:
            pass

        return retval




        
    def dump_data(self):
        columns = self.columns
        # header
        print ('\t'.join (columns))
        for row in self.data:
            print ('\t'.join([str(row.get(col,'')) for col in columns]))

