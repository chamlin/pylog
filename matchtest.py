#!/usr/local/bin/python3
import os
import sys
import re



# can be more than one?
retval = {}
s = 'blah blah blah size=18727(29%) rss=18353(28%) anon=18209(28%) file=54(0%) forest=938(1%) cache=20480(32%) registry=7(0%)'
r = re.compile ('(\w+)=(\d+)\((\d+)%\)')
for stat in r.findall (s):
    name = stat[0]
    retval[name+'-mb'] = stat[1]
    retval[name+'-percent'] = stat[2]




print(retval)

