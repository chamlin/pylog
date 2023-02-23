import sys
import re


# individual functions here for extraction

def shorten_stand (stand_path):
    parts = stand_path.split ('/')
    if len(parts) > 1:
        return parts[-2] + '/' + parts[-1]
    else:
        return stand_path

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
          'general-extract': {'init': {'event': 'on-disk-stand-end'}, 'names': ['stand'], 'regex': '~OnDiskStand (.*)'},
          'tests': ['~OnDiskStand /var/replica-prod/Forests/P_initial_r11_04/00019082'],
          'post-process': {'stand': [shorten_stand]}
        },
        { 'starts': '~InMemoryStand',
          'general-extract': {'init': {'event': 'in-memory-stand-end'}, 'names': ['stand'], 'regex': '~InMemoryStand (.*?)(, .*)?$'},
          'tests': [
            '~InMemoryStand /Users/chamlin/Library/Application Support/MarkLogic/Data/Forests/Meters/00000fa7, indexes storage used % : rangeIndex=5%, reverseIndex=0%, tripleIndex=100%, geospatialRegionIndex=2%',
            '~InMemoryStand /MarkLogic_Data/Forests/P_smartws_r2_02/0001191c'
          ],
          'post-process': {'stand': [shorten_stand]}
        }
    ],
    '[': [
        { 'starts': '[Event:id=Reindexer Trace]',
          'general-extract': {'init': {'event': 'reindexer'}, 'names': ['reason', 'fragments', 'duration', 'rate', 'forest'], 'regex': '.*Refragmented (.+) (\d+) fragments in (\d+) sec at (\d+) .* forest (.*)'},
          'tests': ['[Event:id=Reindexer Trace] Refragmented new fields 10002 fragments in 58 sec at 171 fragments/sec on forest P_initial_p25_01']
        }
    ],
    'D': [
        { 'starts': 'Deleted ',
          'general-extract': {'init': {'event': 'stand-deleted'}, 'names': ['size', 'rate', 'stand'], 'regex': 'Deleted (\d+) MB at (\d+) MB/sec (.*)'},
          'tests': ['Deleted 25 MB at 7066 MB/sec /var/opt/MarkLogic/Forests/Meters/00004222'],
          'post-process': {'stand': [shorten_stand]}
        }
    ],
    'F': [
        # TODO extract %s?,   is this the right event name?
        { 'starts': 'Forest::insert: ',
          'general-extract': {'init': {'event': 'in-memory-full'}, 'names': ['forest', 'code'], 'regex': 'Forest::insert: (\S+) (XDMP-.+?FULL): '},
          'tests': ['Forest::insert: Meters XDMP-INMMTRPLFULL: In-memory triple storage full; list: table=6%, wordsused=7%, wordsfree=91%, overhead=2%; tree: table=1%, wordsused=15%, wordsfree=85%, overhead=0%']
        },
        # TODO extract %s?,   is this the right event name?
        { 'starts': 'Forest::doInsert: ',
          'general-extract': {'init': {'event': 'in-memory-full'}, 'names': ['code'], 'regex': 'Forest::doInsert: (XDMP-.+?FULL): '},
          'tests': ['Forest::doInsert: XDMP-INMMTREEFULL: In-memory tree storage full; list: table=1%, wordsused=30%, wordsfree=68%, overhead=2%; tree: table=16%, wordsused=100%, wordsfree=0%, overhead=0%']
        }
    ],
    'I': [
        { 'starts': 'InMemoryStand ',
          'general-extract': {'init': {'event': 'in-memory-stand'}, 'names': ['stand', 'disk', 'memory', 'list', 'tree', 'rangeIndex', 'reverseIndex', 'tripleIndex', 'geospatialRegionIndex'],
                'regex': 'InMemoryStand (.*), disk=(\d+)MB, memory=(\d+)MB, list=(\d+)MB, tree=(\d+)MB, rangeIndex=(\d+)MB, reverseIndex=(\d+)MB, tripleIndex=(\d+)MB, geospatialRegionIndex=(\d+)MB'},
          'tests': ['InMemoryStand /Users/chamlin/Library/Application Support/MarkLogic/Data/Forests/Meters/00000fa9, disk=1MB, memory=457MB, list=48MB, tree=24MB, rangeIndex=16MB, reverseIndex=16MB, tripleIndex=384MB, geospatialRegionIndex=16MB'],
          'post-process': {'stand': [shorten_stand]}
        },
        { 'starts': 'IndexerEnv::putRangeIndex: XDMP-',
          'general-extract': {'init': {'event': 'put-range-index'}, 'names': ['code'], 'regex': 'XDMP-.* (XDMP-[^:]+)'},
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
          'general-extract': {'init': {'event': 'merged'}, 'names': ['size', 'rate', 'stand'], 'regex': 'Merged (\d+) MB(?: in \d+ sec)? at (\d+) MB/sec to (.*)'},
          'tests': [
              'Merged 6 MB at 25 MB/sec to /var/opt/MarkLogic/Forests/rddr-content-1/00003c60',
              'Merged 51 MB in 2 sec at 25 MB/sec to /var/opt/MarkLogic/Forests/Meters/0000418d'
          ],
          'post-process': {'stand': [shorten_stand]}
        },
        { 'starts': 'Merging ',
          'extract': mergingfun,
          'tests': [
            'Merging 83 MB from /var/opt/MarkLogic/Forests/Meters/00004197, /var/opt/MarkLogic/Forests/Meters/00004198, and /var/opt/MarkLogic/Forests/Meters/00004196 to /var/opt/MarkLogic/Forests/Meters/0000419a, timestamp=16488943209770340',
            'Merging 37 MB from /var/opt/MarkLogic/Forests/Meters/00004182 and /var/opt/MarkLogic/Forests/Meters/00004180 to /var/opt/MarkLogic/Forests/Meters/00004184, timestamp=16488943209770340'
          ],
          'post-process': {'stand': [shorten_stand]}
        }

    ],
    'O': [
        { 'starts': 'OnDiskStand',
          'general-extract': {'init': {'event': 'on-disk-stand'}, 'names': ['stand', 'disk', 'edisk', 'memory'], 'regex': 'OnDiskStand (.*), disk=(\d+)MB, edisk=(\d+)MB, memory=(\d+)MB'},
          'tests': ['OnDiskStand /MarkLogic_Data/Forests/P_initial_p23_04/00058661, disk=201MB, edisk=0MB, memory=16MB'],
          'post-process': {'stand': [shorten_stand]}
        }
    ],
    'R': [
        { 'starts': 'Refragmented',
          'general-extract': {'init': {'event': 'reindexer'}, 'names': ['reason', 'fragments', 'duration', 'rate', 'forest'], 'regex': 'Refragmented (.+) (\d+) fragments in (\d+) sec at (\d+) .* forest (.*)'},
          'tests': ['Refragmented new fields 10000 fragments in 20 sec at 496 fragments/sec on forest P_smartws_p2_04']
        }
    ],
    'S': [
        { 'starts': 'Saving ',
          'general-extract': {'init': {'event': 'saving-stand'}, 'names': 'stand', 'regex': 'Saving (.+)'},
          'tests': ['Saving /var/opt/MarkLogic/Forests/rddr-content-1/00003c5b'],
          'post-process': {'stand': [shorten_stand]}
        },
        { 'starts': 'Saved ',
          'general-extract': {'init': {'event': 'saved-stand'}, 'names': ['size', 'rate', 'stand'], 'regex': 'Saved (\d+) MB(?: in \d+ sec)? at (\d+) MB/sec to (.*)'},
          'tests': ['Saved 10 MB at 119 MB/sec to /var/opt/MarkLogic/Forests/rddr-content-1/00003c61'],
          'post-process': {'stand': [shorten_stand]}
        }
    ]
}

# master blaster, using configs

def extract_events (line):
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
    for extracter in extract_config.get (line[0], []):
        if line.startswith (extracter.get('starts', 'dOnTmAtCh')):
            if 'extract' in extracter:
                extract = extracter.get('extract')(line)
            else:
                params = extracter.get('general-extract')
                extract = generalfun(params['init'], line, params['regex'], params['names'])
            #extract = exfun(line)
            if extract and 'post-process' in extracter:
                for event in extract:
                    for name in extracter.get('post-process'):
                        for processor in extracter['post-process'][name]:
                            event[name] = processor(event[name])
            # TODO stop if continue false and match?
            if extract:
                retval += extract
    return retval

