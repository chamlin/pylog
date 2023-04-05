#!/usr/local/bin/python3
import os
import sys
import argparse
import json

import pyfile as log

parser = argparse.ArgumentParser(description='parse ML error, access, request logs')
parser.add_argument('-c', '--config', help='config file for file paths', required=True)
#parser.add_argument('-t', '--text', help='save the text of the lines (true,false), default is false', default='false')
#parser.add_argument('-d', '--debug', help='comma separated options')

args = vars(parser.parse_args())

with open(args['config'], 'r') as jfile:
    j = json.load(jfile)

# save args and parsed config separately
config = {'args': args, 'config': j}

logs = log.mllogs (config)
logs.read_data()
logs.dump_data()

print ("\n\nfile stats:\n", file=sys.stderr, flush=True)
print (logs, file=sys.stderr, flush=True)

