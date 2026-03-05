#!/opt/homebrew/bin/python3
#!/usr/local/bin/python3
import os
import sys
import argparse
import json

import pyfile as log

parser = argparse.ArgumentParser(description='parse ML error, access, request logs')
parser.add_argument('-c', '--config', help='config file for file paths', required=True)
parser.add_argument('-t', '--text', action='store_true', help='save the text of the lines (true,false), default is false', default='false')
parser.add_argument('-d', '--debug', help='comma separated options')

args = vars(parser.parse_args())

with open(args['config'], 'r') as jfile:
    config = json.load(jfile)

logs = log.mllogs (args, config)
logs.read_data()
logs.dump_data()

if logs.am_debugging ('file-stats'):
        print ("\n\nfile stats:\n", file=sys.stderr, flush=True)
        print (logs, file=sys.stderr, flush=True)

