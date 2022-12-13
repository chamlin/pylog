#!/usr/local/bin/python3

import pyfile as log

file_config = {
    '1': 'foo,bar,.',
    '2': 'bingo, bango'
}
logs = log.mllogs (file_config)
logs.check_config()
print (logs)
