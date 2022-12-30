import sys
import re


# individual functions here for extraction

# returns multiple events, one for each stand mentioned
def mergingfun (line):
    retval = list()
    groups = (re.findall (r'Merging (\d+) MB from (.*) to (.*), timestamp=(\d+)', line))[0]
    if len(groups) < 4:
        return list()
    else:
        retval.append ({'event': 'merge-to', 'stand': groups[2], 'size': groups[0], 'timestamp': groups[3]})
        for stand in re.split ('(?:, | and )', groups[1]):
            retval.append ({'event': 'merge-from', 'stand': stand})
        return retval

def memfun (line):
    retval = {'event': 'memory-logging'}
    extracted = False
    for stat in re.findall (r'(\w+)=(\d+)\((\d+)%\)', line):
        name = stat[0]
        retval[name+'-mb'] = stat[1]
        retval[name+'-percent'] = stat[2]
        extracted = True
    return [retval] if extracted else []

# init should have initialized dict; at least event-name
# names can be str or list of str
def generalfun (init, line, regex, names):
    names = [names] if isinstance(names, str) else names
    extracted = False
    result = re.findall (regex, line)[0]
    #print ('line: ', line, '. regex: ', regex)
    if isinstance(result, str):
        result = [result]
    retval = dict(init)
    if result:
        for i in range(len(names)):
            retval[names[i]] = result[i]
        return [retval]
    return []


# here are the configs to control extraction

# in to extract:  text of line
# out from extract:  list of dicts, each an event with 'event' and some other value(s)
# tests:  array of test lines to check functioning
extract_config = {


    '[': [
        { 'starts': '[Event:id=Reindexer Trace]',
          'general-extract': {'init': {'event': 'reindexer'}, 'names': ['reason', 'fragments', 'duration', 'rate', 'forest'], 'regex': '.*Refragmented (.+) (\d+) fragments in (\d+) sec at (\d+) .* forest (.*)'},
          'tests': ['[Event:id=Reindexer Trace] Refragmented new fields 10002 fragments in 58 sec at 171 fragments/sec on forest P_initial_p25_01']
        }
    ],
    'D': [
        { 'starts': 'Deleted ',
          'general-extract': {'init': {'event': 'deleted-stand'}, 'names': ['size', 'rate', 'stand'], 'regex': 'Deleted (\d+) MB at (\d+) MB/sec (.*)'},
          'tests': ['Deleted 25 MB at 7066 MB/sec /var/opt/MarkLogic/Forests/Meters/00004222']
        }
    ],
    'M': [
        { 'starts': 'Memory ',
          'extract': memfun,
          'tests': ['Memory size=18727(29%) rss=18353(28%) anon=18209(28%) file=54(0%) forest=938(1%) cache=20480(32%) registry=7(0%)']
        },
        { 'starts': 'Merged ',
          'general-extract': {'init': {'event': 'merged'}, 'names': ['size', 'rate', 'stand'], 'regex': 'Merged (\d+) MB(?: in \d+ sec)? at (\d+) MB/sec to (.*)'},
          'tests': [
              'Merged 6 MB at 25 MB/sec to /var/opt/MarkLogic/Forests/rddr-content-1/00003c60',
              'Merged 51 MB in 2 sec at 25 MB/sec to /var/opt/MarkLogic/Forests/Meters/0000418d'
          ]
        },
        { 'starts': 'Merging ',
          'extract': mergingfun,
          'tests': [
            'Merging 83 MB from /var/opt/MarkLogic/Forests/Meters/00004197, /var/opt/MarkLogic/Forests/Meters/00004198, and /var/opt/MarkLogic/Forests/Meters/00004196 to /var/opt/MarkLogic/Forests/Meters/0000419a, timestamp=16488943209770340',
            'Merging 37 MB from /var/opt/MarkLogic/Forests/Meters/00004182 and /var/opt/MarkLogic/Forests/Meters/00004180 to /var/opt/MarkLogic/Forests/Meters/00004184, timestamp=16488943209770340'
          ]
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
          'tests': ['Saving /var/opt/MarkLogic/Forests/rddr-content-1/00003c5b']
        },
        { 'starts': 'Saved ',
          'general-extract': {'init': {'event': 'saved-stand'}, 'names': ['size', 'rate', 'stand'], 'regex': 'Saved (\d+) MB(?: in \d+ sec)? at (\d+) MB/sec to (.*)'},
          'tests': ['Saved 10 MB at 119 MB/sec to /var/opt/MarkLogic/Forests/rddr-content-1/00003c61']
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
            # TODO stop if continue false and match?
            if extract:
                retval += extract
    return retval

