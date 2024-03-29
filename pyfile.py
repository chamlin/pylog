import os
import re
import json
import sys

# for the line work
import lineparse

class mllog:

    def __init__(self, node, path, port=None, type='unknown'):
        self.node = node
        self.path = path
        # type (file, dir; error, request, access, unknown, none)
        self.type = type
        self.lines_read = 0
        self.lines_bad = 0
        self.port = port

    def __str__(self):
        if self.lines_read == 0:
            return f"file: {self.path} (node {self.node}, type {self.type}, port {self.port})"
        else:
            return f"file: {self.path} (node {self.node}, type {self.type}, port {self.port}), {self.lines_bad}/{self.lines_read} lines bad"

class mllogs:

    def __init__(self, config):
        # yeah, dump here, config starts containing args and parsed config
        self.config = config['config']
        if self.am_debugging('config'):  print (f'config in: {config}.', file=sys.stderr, flush=True)
        self.files = {}
        self.data = []
        self.columns = {}
        self.months = {'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6, 'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12}
        # defaults here
        if not 'line-limit' in self.config:  self.config['line-limit'] = sys.maxsize;
        if not 'text' in self.config:  self.config['text'] = False;

        # do some init stuff
        self.column_order = self.init_leading_columns(['datetime', 'node', 'event', 'log-type', 'level'])
        # do some stuff
        self.parse_file_config (self.config['files'])
        self.detect_file_types ()
        self.get_port_numbers ()


    def __str__(self):
        s = ""
        s += f'total rows: {len(self.data)}\n'
        for key in self.files:
            s += f"{key}:     " + str (self.files[key]) + "\n"
        return s

    def am_debugging (self, option):
        if 'debug' in self.config:
            return option in self.config['debug']
        else:
            return False

    def read_data (self):
        self.read_files ()

    def init_leading_columns (self, order):
        column_ratings = {}
        for num, name in [[col, order[col]] for col in range(len(order))]:
            column_ratings[name] = f"!{num:04d}"
        return lambda colname: column_ratings.get(colname, colname)

    def parse_file_config (self, config):
        #print ('file configs: ', self.config['config']['files'], file=sys.stderr, flush=True)
        # set up basic
        for config in self.config['files']:
            if not 'node' in config:  config['node'] = 'X'
            paths = config['path'].split(',')
            node = config['node']
            port_given = config.get ('port', None)
            for path in paths:
                path = path.strip()
                # add then expand if needed
                log = mllog (node, path, port_given)
                if path in self.files:
                    print (f'Ignoring file for "{path}", duplicate.', file=sys.stderr, flush=True)
                    continue
                else:
                    self.files[path] = log
                if os.path.isfile (path):
                    log.type = 'file'
                elif os.path.isdir (path):
                    log.type = 'dir'
                    # get the files and add them too
                    for root, dirs, files in os.walk(path):
                        for filename in files:
                            path = os.path.join(root, filename)
                            if path in self.files:
                                print (f'Ignoring file for "{path}", duplicate.', file=sys.stderr, flush=True)
                            else:
                                self.files[path] = mllog (node, path, type='file')
                else:
                    log.type = 'unknown'

    def get_port_numbers (self):
        for key, file in self.files.items():
            # order dependent
            if file.port is not None: continue
            filename = re.sub ('.*/', '', file.path)
            port_regex = re.compile ('^(?P<port>\d\d\d\d\d?)_')
            try:
                m = port_regex.match(filename)
                port = m.group('port')
                file.port = port
            except Exception as e:
                pass

    def detect_file_types(self):
        error_regex = re.compile ('\d\d\d\d-\d\d-\d\d \d\d:\d\d:\d\d\.\d+ (Finest|Finer|Fine|Debug|Config|Info|Notice|Warning|Error|Critical|Alert|Emergency): ')
        access_regex = re.compile ('\S+\s\S+\s\S+\s\[\d+/\w+/\d\d\d\d:\d\d:\d\d:\d\d.*HTTP')
        
        for key, file in self.files.items():
            if file.type != 'file': continue
            with open(file.path, 'r', encoding='UTF-8') as afile:
                lines = 0
                try:
                    while (line := afile.readline().rstrip()):
                        if lines > 10:
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
        if self.am_debugging('file-reads'):  print ("Reading files", file=sys.stderr, flush=True)
        for key, file in self.files.items():
            if file.type == 'request':
                self.read_request_file (file)
            elif file.type == 'access':
                self.read_access_file (file)
            elif file.type == 'error':
                self.read_error_file (file)
        # just keep the keys
        self.columns = sorted(self.columns.keys(), key=self.column_order)

    def read_request_file (self, file):
        if self.am_debugging('file-reads'):  print ("> " + file.path, file=sys.stderr, flush=True)
        with open(file.path, 'r', encoding='UTF-8') as request_file:
            lines_read, lines_bad = [0, 0]
            while (line := request_file.readline().rstrip()):
                lines_read += 1
                try:
                    vals = json.loads (line)
                    vals['datetime'] = re.sub('-\d\d:\d\d','',vals.pop('time'))
                    vals['node'] = file.node
                    # TODO - genericize?
                    vals['event'] = 'request'
                    vals['log-path'] = file.path
                    vals['log-type'] = file.type
                    if file.port is not None:
                        vals['port'] = file.port
                    vals['log-line'] = lines_read
                    if self.config['text']: vals['text'] = line
                    self.columns.update(vals)   
                    self.data.append(vals)
                except Exception as e:
                    lines_bad += 1
                    if self.am_debugging ('unclassified'):  print (f"Error in parse of line in {file.path} #{line}: {e}.", file=sys.stderr, flush=True)
        file.lines_read = lines_read
        file.lines_bad = lines_bad
        if self.am_debugging('file-reads'):  print ("< " + file.path, file=sys.stderr, flush=True)


    def read_access_file (self, file):
        access_regex = re.compile ('(\S+)\s(\S+)\s(\S+)\s\[(\d+)/(\w+)/(\d\d\d\d):(\d\d):(\d\d):(\d\d) ([^]]+)\] "(\w+) (\S+) (\S+)" (\d+) (\S+) (\S+) "([^"]+)"')
        access_columns = ('ip', 'thing', 'user', 'day', 'month', 'year', 'hour', 'minute', 'second', 'timezone', 'method', 'URL', 'protocol', 'response', 'bytes', 'referrer', 'client')
        access_columns_dropped = ('day', 'month', 'year', 'hour', 'minute', 'second', 'timezone')
        external_user_regex = re.compile ('External User\((.*)\) is Mapped to Temp User\((.*)\) with Role\(s\): (.*)')
        external_user_columns = ('external-user', 'temp-user', 'user-roles')
        queued_external_auth_lines = list()

        if self.am_debugging('file-reads'):  print ("> " + file.path, file=sys.stderr, flush=True)
        with open(file.path, 'r', encoding='UTF-8') as request_file:
            lines_read, lines_bad = [0, 0]
            while (line := request_file.readline().rstrip()):
                lines_read += 1
                if lines_read >= self.config['line-limit']:
                    break
                try:
                    vals = {'log-path': file.path, 'log-type': file.type, 'log-line': lines_read, 'node': file.node}
                    if self.config['text']: vals['text'] = line
                    if file.port is not None: vals['port'] = file.port
                    m = access_regex.match(line)
                    if m is not None:
                        # TODO - genericize?
                        # TODO - save timezone?
                        vals['event'] = 'access'
                        for index in range(len(access_columns)):
                            vals[access_columns[index]] = m.group(index+1)
                        vals['datetime'] = f"{int(vals['year']):04d}-{self.months[vals['month']]:02d}-{int(vals['day']):02d}"
                        vals['datetime'] += f" {int(vals['hour']):02d}:{int(vals['minute']):02d}:{int(vals['second']):02d}"
                        for dropped_column in access_columns_dropped:
                            vals.pop(dropped_column)
                        self.columns.update(vals)   
                        self.data.append(vals)
                        # have a datetime so clear out any queued external auth lines
                        for queued in queued_external_auth_lines:
                            queued['datetime'] = vals['datetime']
                            self.columns.update(queued)   
                            self.data.append(queued)
                        queued_external_auth_lines = list()
                    else:
                        m = external_user_regex.match(line)
                        vals['event'] = 'external-auth'
                        if m is not None:
                            for index in range(len(external_user_columns)):
                                vals[external_user_columns[index]] = m.group(index+1)
                            queued_external_auth_lines.append(vals)
                        else:
                            lines_bad += 1
                            if self.am_debugging ('unclassified'):
                                print (f"Unclassified line from access file {file.path}: " + line,  file=sys.stderr, flush=True)
                except Exception as oops:
                    lines_bad += 1
                    if self.am_debugging ('unclassified'):
                        print (f"Error on line from access file {file.path}: " + line,  file=sys.stderr, flush=True)
                        print (oops, file=sys.stderr, flush=True)
        file.lines_read = lines_read
        file.lines_bad = lines_bad
        if self.am_debugging('file-reads'):  print ("< " + file.path, file=sys.stderr, flush=True)

    def read_error_file (self, file):

        if self.am_debugging('file-reads'):  print ("> " + file.path, file=sys.stderr, flush=True)
        with open(file.path, 'r', encoding='UTF-8') as request_file:
            lines_read, lines_bad = [0, 0]
            while (line := request_file.readline().rstrip()):
                lines_read += 1
                rows_out = self.classify_error_line(file, line, lines_read)
                if len(rows_out) > 0:
                    for row in rows_out:
                        self.data.append(row)
                        self.columns.update(row)
                else:
                    if self.am_debugging ('unclassified'):  print(f"Couldn't classify line from file {file.path}, #{lines_read}: " + line,  file=sys.stderr, flush=True)
                    lines_bad += 1
                if lines_read >= self.config['line-limit']:
                    break
        file.lines_read = lines_read
        file.lines_bad = lines_bad
        if self.am_debugging('file-reads'):  print ("< " + file.path, file=sys.stderr, flush=True)

    def classify_error_line (self, file, line, line_number):
        prefix_regex = re.compile ('(?P<datetime>\d\d\d\d-\d\d-\d\d \d\d:\d\d:\d\d\.\d+) (?P<level>\S+):\s(?P<text>.*)')
        # return list of extracted rows.  0 means error or bad line, whatever
        retval = list()

        try:
            m = prefix_regex.match(line)
            text = m.group('text')
            # TODO - genericize?
            vals = {'log-path': file.path, 'log-type': file.type, 'log-line': line_number, 'datetime': m.group('datetime'), 'node': file.node, 'level': m.group('level')}
            if self.config['text']: vals['text'] = text
            # OK here?
            events = lineparse.extract_events(self.am_debugging('extract'), text)
            if len(events) == 0:
                vals['event'] = 'unknown'
                if self.am_debugging('unclassified'):
                    print (f'Unclassified line: {line}.', file=sys.stderr, flush=True)
                retval.append (vals)
            else:
                for event in events:
                    event.update (vals)
                    retval.append (event)
        except Exception as e:
            # TODO Avoid error when continued line as   Bad line from access file testdir/TaskServer_ErrorLog_6.txt, #15: 2022-12-06 10:36:52.768 Notice:+in /log.xqy, at 7:10 [1.0-ml]
            if self.am_debugging('unclassified'):
                print (f"Error in classification of line in {file.path} #{line_number}: {e}", file=sys.stderr, flush=True)

        return retval


        
    def dump_data(self):
        columns = self.columns
        # header
        print ('\t'.join (columns))
        for row in self.data:
            vals = [str(row.get(column,'')) for column in columns]
            print ('\t'.join(vals))

