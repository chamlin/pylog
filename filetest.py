#!/usr/local/bin/python3
import os
import sys
import argparse
import json

import pyfile as log

parser = argparse.ArgumentParser(description='parse ML error, access, request logs')
parser.add_argument('-c', '--config', help='config file for file paths')
parser.add_argument('-d', '--debug', help='comma separated options')

args = parser.parse_args()

with open(args.config, 'r') as jfile:
    j = json.load(jfile)

logs = log.mllogs (j)
logs.read_data()
logs.dump_data()

