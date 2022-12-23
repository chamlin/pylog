import re


# individual functions here for extraction

def memfun (line):
    retval = {'event-type': 'memory-logging'}
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
# out from extract:  list of dicts, each an event with 'event-type' and some other value(s)
# tests:  array of test lines to check functioning
extract_config = {
    'D': [
        { 'starts': 'Deleted ',
          'general-extract': {'init': {'event-type': 'deleted-stand'}, 'names': ['size', 'rate', 'stand'], 'regex': 'Deleted (\d+) MB at (\d+) MB/sec (.*)'},
          'tests': ['Deleted 25 MB at 7066 MB/sec /var/opt/MarkLogic/Forests/Meters/00004222']
        }
    ],
    'M': [
        { 'starts': 'Memory ',
          'extract': memfun,
          'tests': ['Memory size=18727(29%) rss=18353(28%) anon=18209(28%) file=54(0%) forest=938(1%) cache=20480(32%) registry=7(0%)']
        },
        { 'starts': 'Merged ',
          'general-extract': {'init': {'event-type': 'merged'}, 'names': ['size', 'rate', 'stand'], 'regex': 'Merged (\d+) MB(?: in \d+ sec)? at (\d+) MB/sec to (.*)'},
          'tests': [
              'Merged 6 MB at 25 MB/sec to /var/opt/MarkLogic/Forests/rddr-content-1/00003c60',
              'Merged 51 MB in 2 sec at 25 MB/sec to /var/opt/MarkLogic/Forests/Meters/0000418d'
          ]
        }
    ],
    'S': [
        { 'starts': 'Saving ',
          'general-extract': {'init': {'event-type': 'saving-stand'}, 'names': 'stand', 'regex': 'Saving (.+)'},
          'tests': ['Saving /var/opt/MarkLogic/Forests/rddr-content-1/00003c5b']
        },
        { 'starts': 'Saved ',
          'general-extract': {'init': {'event-type': 'saved-stand'}, 'names': ['size', 'rate', 'stand'], 'regex': 'Saved (\d+) MB(?: in \d+ sec)? at (\d+) MB/sec to (.*)'},
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
    A list of dictionaries, with event-type and some other value(s)
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

