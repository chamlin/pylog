#!/usr/local/bin/python3

import lineparse

for key in sorted(lineparse.extract_config.keys()):
    key_config = lineparse.extract_config[key]
    print (key + ':')
    for config in key_config:
        for test in config['tests']:
            print (test)
            print (lineparse.extract_events(test))

