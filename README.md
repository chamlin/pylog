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

## config.json, config2.json

example config files; fix for your data

## test-lineparse.py, test-lineparse.out

expected output of test-lineparse.py
