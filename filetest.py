#!/usr/local/bin/python3
import os
import sys

import pyfile as log

file_config = {
    '1': 'node1',
    '2': 'testdir'
}
logs = log.mllogs (file_config)
print (logs, file=sys.stderr, flush=True)
logs.dump_data()
