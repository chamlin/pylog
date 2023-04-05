#!/usr/local/bin/python3

import lineparse

for key in sorted(lineparse.extract_config.keys()):
    key_config = lineparse.extract_config[key]
    print()
    print ('Tests starting for "' + key + '":')
    print()
    for config in key_config:
        for test in config['tests']:
            print (test)
            for event in lineparse.extract_events({'args': {}, 'config': {}}, test):
                print (event)
            print()

