#!/usr/local/bin/python3
import os
import sys
import re

def memfun (line):
    retval = {'event-type': 'memory-logging'}
    extracted = False
    r = re.compile ('(\w+)=(\d+)\((\d+)%\)')
    for stat in r.findall (line):
        extracted = True
        name = stat[0]
        retval[name+'-mb'] = stat[1]
        retval[name+'-percent'] = stat[2]
    return [retval] if extracted else []

# in to extract:  text of line
# out from extract:  list of dicts, each an event with 'event-type' and some other value(s)
# tests:  array of test lines to check functioning
extract_config = {
    'M': [
        { 'starts': 'Memory ',
          'extract': memfun,
          'tests': ['Memory size=18727(29%) rss=18353(28%) anon=18209(28%) file=54(0%) forest=938(1%) cache=20480(32%) registry=7(0%)']
        }
    ]
}


def runfun (line):
    retval = []
    for extracter in extract_config.get (line[0], []):
        if line.startswith (extracter.get('starts', 'dOnTmAtCh')):
            exfun = extracter.get('extract', None)
            extract = exfun(line)
            # TODO stop if continue false and match?
            retval += extract
    return retval


# can be more than one?
s = 'Memory size=18727(29%) rss=18353(28%) anon=18209(28%) file=54(0%) forest=938(1%) cache=20480(32%) registry=7(0%)'
s = 'emory blah'

retval = runfun(s)




print(retval)

