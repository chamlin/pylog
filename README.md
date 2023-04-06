# pylog
python, log analyzer for MarkLogic

# why/what

To get the error log and app server access and request logs extracted together.

Output to tsv and then whatever you like.

Also some basic plots and extracts.

# scripts

## filetest.py

main test file; run for options

Extracts to stdout, errors/warnings to stderr

## test-plots.py

plot numeric values in a stack, per node

## lineparse.py

module for error-log parsing

## test-lineparse.py

script to run the tests in lineparse.py

# files

## examples.ipynb

jupyter, basic manipulations of the data

## config.json, config2.json

example config files; fix for your data

### settings

#### file mapping

gives node and path.  path can be a file or a dir (includes all sub dirs/files)

    "files": [
        { "node": "002", "path": "foo" }
    ],

if no node name given, 'X' is used.

#### text

    "text": true,

whether to retain text.  default false.

#### line-limit

    "line-limit": 4

limit for number of lines to read from a file.  default is sys.maxsize.

#### debug

    "debug": ["unclassified","file-stats","extract"],

- config:  config dumped before run
- file-reads:  files read
- unclassified:  unclassified lines
- extract:  extraction


## test-lineparse.py, test-lineparse.out

expected output of test-lineparse.py
