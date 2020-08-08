.. title:: Scripts

Utility scripts
---------------

The package ships with two command-line utility scripts.

`bb2csv`
^^^^^^^^

Blackbox log to CSV converter utility.

*Examples:*

* Export the 2nd session to a file called `btfl_all.2.csv`:

::

    $ bb2csv btfl_all.bbl -i 2 -o btfl_all.2.csv

* Print CSV to stdout with debug info enabled:

::

    $ bb2csv -vvv btfl_all.2.bbl

Help
~~~~

::

    usage: bb2csv [-h] [-o PATH] [-i LOG_INDEX] [-v] path

    positional arguments:
      path                  Path to a blackbox log file

    optional arguments:
      -h, --help            show this help message and exit
      -o PATH, --output PATH
                            Optional path to an output file (otherwise use standard output) (default: None)
      -i LOG_INDEX, --index LOG_INDEX
                            Log index number (In case of merged input) (default: 1)
      -v                    Control verbosity (can be used multiple times) (default: 0)

`bbsplit`
^^^^^^^^^

Split logging sessions into separate files. When using the `-n` or `--dry-run` option it will only output the number of sessions in the file and some additional info.

Output filenames are generated as follows:

::

    ${ORIG_NAME}.${INDEX}.${ORIG_EXT}

*Examples:*

* Split `btfl_all.bbl` into files

::

    $ bbsplit btfl_all.bbl

This will create the following files in the current directory:

::

    btfl_all.1.bbl
    btfl_all.2.bbl
    ...
    btfl_all.[\d]+.bbl

* Do the same but save the output to a directory named `exported`

::

    $ bbsplit -o /path/to/exported btfl_all.bll

Help
~~~~

::

    usage: bbsplit [-h] [-o DIR] [-v] [-n] path

    positional arguments:
      path                  Path to a blackbox log file

    optional arguments:
      -h, --help            show this help message and exit
      -o DIR, --output DIR  Optional path to output directory, defaults to parent directory of the original log file (default: None)
      -v                    Control verbosity (can be used multiple times) (default: 0)
      -n, --dry-run         Do not write anything (default: False)
