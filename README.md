# vogsphere
A helper script for debt redistribution task

## Windows Installation
* Install Python for your system https://www.python.org/downloads/release/python-2711/
* Download lastest vogspere version, unzip to Z://vogsphere
* Check your python installation

```ftype Python.File```
shows you PYTHON_PATH. Usually it defaults to C:\\Python27\python.exe
* (optional) Set console encoding to utf-8. If not you may be unable to specify agents prefix.

## Data processing
Make sure input data matches the following criteria:
* Data is in utf-8 format
* Input csv has commas for delimiters

If input data is in Z://vogsphere/agents_in.csv, cmd command looks like

```C:\\Python27\python.exe agents.py agents_in.csv > out.csv```

## Troubleshooting
Check log.log file for details
