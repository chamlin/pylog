#! /opt/homebrew/bin/python3

from pathlib import Path
import re
import argparse
import json

debugs = []
paths = []

# constant node
def filter_path (path):
    retval = {'path': str (path), 'node': 'x'} 
    return retval

# /Users/hamlin/tickets/01702075-
def xfilter_path (path):
    retval = {} 
    pattern = r'xmledhm(\d+p).aetna.com.*Log'
    p = re.compile (pattern)
    m = p.search (str (path))
    if m:
        retval['path'] = str (path)
        retval['node'] = m.group(1)
        pattern = r'xmledhm\d+p.aetna.com_(\d+)_'
        p = re.compile (pattern)
        m = p.search (str (path))
        if m:  retval['port'] = m.group (1)
    return retval

# /Users/hamlin/tickets/01702075-
def xfilter_path (path):
    retval = {} 
    pattern = r'broadridge/(\d\d)'
    p = re.compile (pattern)
    m = p.search (str (path))
    if m:
        retval['path'] = str (path)
        retval['node'] = 'n' + m.group(1)
    return retval

#base_path = Path('/Users/hamlin/tickets/01554751-') 
def node_filter_path (path):
    retval = {} 
    pattern = r'\d+p$'
    p = re.compile (pattern)
    m = p.search (str (path))
    if m:
        retval['node'] = m.group()
    return retval

def dummy_filter_path (path):
    pattern = r'\.txt$'
    p = re.compile (pattern)
    m = p.search (str (path))
    if m:
        return m.group()
    else:
         return 'x'

parser = argparse.ArgumentParser(prog='create-config.py', description='create config for pylog, create cvs for logs', epilog='')
parser.add_argument ('-p', '--paths', help='comma separated dirs/files')
parser.add_argument ('-d', '--debugs', help='comma separated options')
args = vars (parser.parse_args())

if args['paths']:  paths = args['paths'].split (',')
if args['debugs']:  debugs = args['debugs'].split (',')

if 'args' in debugs:  print ('args: ' + str (args))
if 'debugs' in debugs:  print ('debugs: ' + str (debugs))

found = []

# Use rglob('*') to match all files and folders recursively
#for file_path in base_path.rglob('*'):
for path in paths:
    p = Path (path)
    if 'paths' in debugs:  print (path)
    if p.is_file():
        info = filter_path (p)
        if len (info):  found.append (info)
    if p.is_dir():
        pstr = str (p)
        dir_pattern = pstr + '*' if pstr.endswith ('/') else pstr + '/*'
        for dinge in p.rglob ('*'):
            if 'paths' in debugs:  print (str (dinge))
            if dinge.is_file():
                info = filter_path (dinge)
                if len (info):  found.append (info)


json_paths = [json.dumps (p, indent=4) for p in found]

if len (found):
        print ('{')
        print ('    "files": [')
        print (',\n'.join (json_paths))
        #for file_found in json_paths:  print ('        ' + file_found + ',')
        print ('    ]')
        print ('}')
        

