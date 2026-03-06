import sys
import re
import json


# individual functions here for extraction

def shorten_stand (stand_path):
    parts = stand_path.split ('/')
    if len(parts) > 1:
        return parts[-2] + '/' + parts[-1]
    else:
        return stand_path

def general_trace_event (event_name):
    return 'trace-' + event_name.lower().replace(' ', '-')

# returns multiple events, one for each stand mentioned
def mergingfun (line):
    retval = list()
    groups = (re.findall (r'Merging (\d+) MB from (.*) to (.*), timestamp=(\d+)', line))[0]
    if len(groups) < 4:
        return list()
    else:
        retval.append ({'event': 'merging-to', 'stand': groups[2], 'size': groups[0], 'timestamp': groups[3]})
        for stand in re.split ('(?:, | and )', groups[1]):
            retval.append ({'event': 'merging-from', 'stand': stand})
        return retval

def memfun (line):
    retval = {'event': 'memory-logging'}
    extracted = False
    for stat in re.findall (r'(\w+)=(\d+)\((\d+)%\)', line):
        name = stat[0]
        retval[name+'-mb'] = int(stat[1])
        retval[name+'-percent'] = int(stat[2])
        extracted = True
    retval['huge-anon-swap-file-percent'] = retval.get('huge-percent',0) + retval.get('anon-percent',0) + retval.get('swap-percent',0) + retval.get('file-percent',0)
    retval['forest-cache-percent'] = retval.get('forest-percent',0) + retval.get('cache-percent',0)
    return [retval] if extracted else []

# init should have initialized dict; at least event
# names can be str or list of str
def generalfun (init, line, regex, names):
    names = [names] if isinstance(names, str) else names
    extracted = False
    found = re.findall (regex, line)
    if (len (found) < 1):
        return []
    result = found[0]
    #print ('line: ', line, '. regex: ', regex)
    if isinstance(result, str):
        result = [result]
    retval = dict(init)
    for i in range(len(names)):
        retval[names[i]] = result[i]
    return [retval]


# here are the configs to control extraction

# in to extract:  text of line
# out from extract:  list of dicts, each an event with 'event' and some other value(s)
# tests:  array of test lines to check functioning
extract_config = {


    '~': [
        { 'starts': '~OnDiskStand',
          'general-extract': {'init': {'event': 'on-disk-stand-end'}, 'names': ['stand'], 'regex': r'~OnDiskStand (.*)'},
          'tests': ['~OnDiskStand /var/replica-prod/Forests/P_initial_r11_04/00019082'],
          'post-process': {'stand': [shorten_stand]}
        },
        { 'starts': '~InMemoryStand',
          'general-extract': {'init': {'event': 'in-memory-stand-end'}, 'names': ['stand'], 'regex': r'~InMemoryStand (.*?)(, .*)?$'},
          'tests': [
            '~InMemoryStand /Users/chamlin/Library/Application Support/MarkLogic/Data/Forests/Meters/00000fa7, indexes storage used % : rangeIndex=5%, reverseIndex=0%, tripleIndex=100%, geospatialRegionIndex=2%',
            '~InMemoryStand /MarkLogic_Data/Forests/P_smartws_r2_02/0001191c'
          ],
          'post-process': {'stand': [shorten_stand]}
        }
    ],
    '[': [
        { 'starts': '[Event:id=Reindexer Trace]',
          'general-extract': {'init': {'event': 'reindexer'}, 'names': ['reason', 'fragments', 'duration', 'rate', 'forest'], 'regex': r'.*Refragmented (.+) (\d+) fragments in (\d+) sec at (\d+) .* forest (.*)'},
          'tests': ['[Event:id=Reindexer Trace] Refragmented new fields 10002 fragments in 58 sec at 171 fragments/sec on forest P_initial_p25_01']
        },
        { 'starts': '[Event:id=',
          'general-extract': {'init': {}, 'names': ['event'], 'regex': r'Event:id=([^]]+)'},
          'tests': ['[Event:id=General Name] Just a test of the general fallback trace event extraction'],
          'post-process': {'event': [general_trace_event]}
        }
    ],


    'C': [
        { 'starts': 'Closing journal ',
          'literal-extract': [{'event': 'journals'}],
          'tests': [
                'Closing journal /data/MarkLogic/Forests/gptm-prod-01-f-content-001-2/Jou ...',
          ]
        },
        { 'starts': 'Creating journal archive',
          'literal-extract': [{'event': 'journal-archiving'}],
          'tests': [
                'Creating journal archive /backup/gptm-prod-01-f-content/20260301-230...',
          ]
        },
    ],
    'D': [
        { 'starts': 'Deleted ',
          'general-extract': {'init': {'event': 'stand-deleted'}, 'names': ['size', 'rate', 'stand'], 'regex': r'Deleted (\d+) MB at (\d+) MB/sec (.*)'},
          'tests': ['Deleted 25 MB at 7066 MB/sec /var/opt/MarkLogic/Forests/Meters/00004222'],
          'post-process': {'stand': [shorten_stand]}
        },
        { 'starts': 'Deadlock detected ',
          'literal-extract': [{'event': 'deadlock'}],
          'tests': ['Deadlock detected locking gptm-prod-01-f-content-001-2 /Transaction/GLOSS/00000000000790466009/1.xml']
        },
        { 'starts': 'Detecting indexes ',
          'literal-extract': [{'event': 'detecting-indexes'}],
          'tests': ['Detecting indexes for database Documents']
        },
        { 'starts': 'Detected indexes ',
          'literal-extract': [{'event': 'detecting-indexes'}],
          'tests': ['Detected indexes for database Documents: ws, fp, fcs, fds, few, fep, sln']
        }
    ],
    'F': [
        # TODO extract %s?,   is this the right event name?
        { 'starts': 'Forest ',
          'general-extract': {'init': {'event': 'journals'}, 'names': ['forest'],
                'regex': r'Forest (\S+) (opening recycled|purging journal|RecoveryManager) '},
          'tests': [
                'Forest gptm-prod-01-f-content-rep1-012-2 opening recycled journal file /data/MarkLogic/Forests/gptm-prod-01-f-cont...',
                'Forest Meters RecoveryManager wrote end cap'
          ]
        },
        { 'starts': 'Forest ',
          'general-extract': {'init': {'event': 'min-query-timestamp'}, 'names': ['forest','timestamp'], 'regex': r'Forest (\S+) setting minQueryTimestamp to (\d+)'},
          'tests': ['Forest gptm-prod-01-f-content-001-1 setting minQueryTimestamp to 17724615710661000 due to merge']
        },
        { 'starts': 'Forest::insert: ',
          'general-extract': {'init': {'event': 'in-memory-full'}, 'names': ['forest', 'code'], 'regex': r'Forest::insert: (\S+) (XDMP-.+?FULL): '},
          'tests': ['Forest::insert: Meters XDMP-INMMTRPLFULL: In-memory triple storage full; list: table=6%, wordsused=7%, wordsfree=91%, overhead=2%; tree: table=1%, wordsused=15%, wordsfree=85%, overhead=0%']
        },
        { 'starts': 'Forest::doInsert: ',
          'general-extract': {'init': {'event': 'in-memory-full'}, 'names': ['code'], 'regex': r'Forest::doInsert: (XDMP-.+?FULL): '},
          'tests': ['Forest::doInsert: XDMP-INMMTREEFULL: In-memory tree storage ...']
        }
    ],
    'I': [
        { 'starts': 'InMemoryStand ',
          'general-extract': {'init': {'event': 'in-memory-stand'}, 'names': ['stand', 'disk', 'memory', 'list', 'tree', 'rangeIndex', 'reverseIndex', 'tripleIndex', 'geospatialRegionIndex'],
                'regex': r'InMemoryStand (.*), disk=(\d+)MB, memory=(\d+)MB, list=(\d+)MB, tree=(\d+)MB, rangeIndex=(\d+)MB, reverseIndex=(\d+)MB, tripleIndex=(\d+)MB, geospatialRegionIndex=(\d+)MB'},
          'tests': ['InMemoryStand /Users/chamlin/Library/Application Support/MarkLogic/Data/Forests/Meters/00000fa9, disk=1MB, memory=457MB, list=48MB, tree=24MB, rangeIndex=16MB, reverseIndex=16MB, tripleIndex=384MB, geospatialRegionIndex=16MB'],
          'post-process': {'stand': [shorten_stand]}
        },
        { 'starts': 'IndexerEnv::putRangeIndex: XDMP-',
          'general-extract': {'init': {'event': 'put-range-index'}, 'names': ['code'], 'regex': r'XDMP-.* (XDMP-[^:]+)'},
          'tests': ['IndexerEnv::putRangeIndex: XDMP-RANGEINDEX: Range index error: long fn:doc("/at/ksv/current/orders/9b0ca175-e26b-e86d-2151-00a49da8db01.xml")/*:customerorder/*:orderEntity/*:zip: XDMP-LEXVAL: Invalid lexical value ""']
        }
    ],
    'M': [
        { 'starts': 'Memory ',
          'extract': memfun,
          'tests': [
              'Memory size=18727(29%) rss=18353(28%) anon=18209(28%) file=54(0%) forest=938(1%) cache=20480(32%) registry=7(0%)',
              'Memory 27% phys=772438 size=327735(42%) rss=96046(12%) huge=116584(15%) anon=18172(2%) file=192331(24%) forest=226365(29%) cache=81920(10%) registry=1(0%)'
          ]

        },
        { 'starts': 'Merged ',
          'general-extract': {'init': {'event': 'merged'}, 'names': ['size', 'rate', 'stand'], 'regex': r'Merged (\d+) MB(?: in \d+ sec)? at (\d+) MB/sec to (.*)'},
          'tests': [
              'Merged 6 MB at 25 MB/sec to /var/opt/MarkLogic/Forests/rddr-content-1/00003c60',
              'Merged 51 MB in 2 sec at 25 MB/sec to /var/opt/MarkLogic/Forests/Meters/0000418d'
          ],
          'post-process': {'stand': [shorten_stand]}
        },
        { 'starts': 'Merging ',
          'general-extract': {'init': {'event': 'merging'}, 'names': ['size', 'stand', 'timestamp'], 'regex': r'Merging (\d+) MB from .* to (.*), timestamp=(\d+)'},
          'tests': [
            'Merging 83 MB from /var/opt/MarkLogic/Forests/Meters/00004197, /var/opt/MarkLogic/Forests/Meters/00004198, and /var/opt/MarkLogic/Forests/Meters/00004196 to /var/opt/MarkLogic/Forests/Meters/0000419a, timestamp=16488943209770340',
            'Merging 37 MB from /var/opt/MarkLogic/Forests/Meters/00004182 and /var/opt/MarkLogic/Forests/Meters/00004180 to /var/opt/MarkLogic/Forests/Meters/00004184, timestamp=16488943209770340'
          ],
          'post-process': {'stand': [shorten_stand]}
        },
        { 'starts': 'Memory low',
          'literal-extract': [{'event': 'memory-low'}],
          'tests': [
              'Memory low: huge+anon+swap+file=92%phys'
          ]
        },

    ],
    'O': [
        { 'starts': 'OnDiskStand',
          'general-extract': {'init': {'event': 'on-disk-stand'}, 'names': ['stand', 'disk', 'edisk', 'memory'], 'regex': r'OnDiskStand (.*), disk=(\d+)MB, edisk=(\d+)MB, memory=(\d+)MB'},
          'tests': ['OnDiskStand /MarkLogic_Data/Forests/P_initial_p23_04/00058661, disk=201MB, edisk=0MB, memory=16MB'],
          'post-process': {'stand': [shorten_stand]}
        }
    ],
    'R': [
        { 'starts': 'Refragmented',
          'general-extract': {'init': {'event': 'reindexer'}, 'names': ['reason', 'fragments', 'duration', 'rate', 'forest'], 'regex': r'Refragmented (.+) (\d+) fragments in (\d+) sec at (\d+) .* forest (.*)'},
          'tests': ['Refragmented new fields 10000 fragments in 20 sec at 496 fragments/sec on forest P_smartws_p2_04']
        },
        { 'starts': 'Retrying ',
          'literal-extract': [{'event': 'retry'}],
          'tests': ['Retrying xdmp:invoke update-transaction-from-transaction-trigger.xqy 10751236092397035323 Update 1 because ']
        }
    ],
    'S': [
        { 'starts': 'Saving ',
          'general-extract': {'init': {'event': 'saving-stand'}, 'names': 'stand', 'regex': r'Saving (.+)'},
          'tests': ['Saving /var/opt/MarkLogic/Forests/rddr-content-1/00003c5b'],
          'post-process': {'stand': [shorten_stand]}
        },
        { 'starts': 'Saved ',
          'general-extract': {'init': {'event': 'saved-stand'}, 'names': ['size', 'rate', 'stand'], 'regex': r'Saved (\d+) MB(?: in \d+ sec)? at (\d+) MB/sec to (.*)'},
          'tests': ['Saved 10 MB at 119 MB/sec to /var/opt/MarkLogic/Forests/rddr-content-1/00003c61'],
          'post-process': {'stand': [shorten_stand]}
        },
        { 'starts': 'Slow ',
          'literal-extract': [{'event': 'slow-message'}],
          'tests': ['Slow fsync /mnt/mldata/Forests/careempower-app-content-1/Label, 1.775 KB in 1.002 sec']
        },
    ],
    'T': [
        { 'starts': 'Termlist for ',
          'general-extract': {'init': {'event': 'termlist'}, 'names': ['size'], 'regex': r'is (\d+) MB;'},
          'tests': ['Termlist for 11363135516565172648 in /data/MarkLogic/Forests/gptm-prod-01-f-content-001-1/00038c0d is 243 MB; will discard positions at 256 MB.']
        },
    ],
    '*': [
        { 'matches': 'Telemetry',
          'literal-extract': [{'event': 'telemetry'}],
          'tests': ['Uploaded 1 records, 1 MB of Usage Data to Telemetry']
        }
    ]
}

# master blaster, using extractors

def extract_events (debug, line):
    '''
    Extracts event info from the text of an ErrorLog line

    Parameters
    ----------
    line : string
        the text of an ErrorLog line (after the 'Level: ' part
    

    Returns
    -------
    A list of dictionaries, with event and some other value(s)
    ''' 
    retval = list()
    # try for starting letter or general ones
    extractors = extract_config.get (line[0], []) + extract_config.get ('*', [])
    for extractor in extractors:
        starts = extractor.get('starts', '*dOnTsTaRt*')
        matches = re.compile(extractor.get('matches', '@dOnTmAtCh@'))
        if debug:  print(f'checking extractor: starts="{starts}" matches="{matches}"', file=sys.stderr, flush=True)
        if line.startswith (starts) or matches.findall (line):
            if debug:  print(f'firing extractor: starts="{starts}" matches="{matches}"', file=sys.stderr, flush=True)
            # do the extract
            if 'literal-extract' in extractor:
                extract = extractor['literal-extract']
            elif 'extract' in extractor:  
                extract = extractor.get('extract')(line)
            else:
                params = extractor.get('general-extract')
                extract = generalfun(params['init'], line, params['regex'], params['names'])
            #extract = exfun(line)
            if extract and 'post-process' in extractor:
                for event in extract:
                    for name in extractor.get('post-process'):
                        for processor in extractor['post-process'][name]:
                            event[name] = processor(event[name])
            # TODO stop if continue false and match?
            if extract:
                retval += extract
                if debug:  print(f'extracted: {extract}.', file=sys.stderr, flush=True)
                # TODO for now, just stop
                break
    return retval

