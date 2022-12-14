#!/usr/local/bin/python3
import os

import pyfile as log

file_config = {
    '1': 'node1',
    '2': 'bingo, testdir'
}
logs = log.mllogs (file_config)
print (logs)
logs.dump_data()
