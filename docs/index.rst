.. title:: orangebox - A Cleanflight/Betaflight blackbox log parser

orangebox
---------

A Cleanflight/Betaflight blackbox log parser written in Python 3. `orangebox` has no dependencies other than the Python standard library. It was roughly modeled after the one in `Blackbox Log Viewer <https://github.com/betaflight/blackbox-log-viewer>`_ hence produces the same output. Merged files (flash chip logs) are supported since version `0.2.0`.

It was reported that `Blackbox Log Viewer <https://github.com/betaflight/blackbox-log-viewer>`_ can ignore a malformed file header and still decode the logged frames. For this reason an `allow_invalid_header` argument was added to `.Parser.load` method and `.Reader` constructor in version `0.4.0`. This option can now also be passed to the CLI tools.

The name "orangebox" comes from the fact that so-called black boxes (flight data recorders) are in fact orange to help the work of search and rescue teams by making it easier to find.

.. image:: https://upload.wikimedia.org/wikipedia/commons/thumb/7/76/Two-In-One_Data_Recorder.JPG/640px-Two-In-One_Data_Recorder.JPG
    :alt: A Cockpit Voice and Data Recorder (CVDR), with its attached ULB visible on the left side of the unit
    :target: https://en.wikipedia.org/wiki/Flight_recorder#/media/File:Two-In-One_Data_Recorder.JPG
    :align: center

Installation
^^^^^^^^^^^^

From package
~~~~~~~~~~~~

For normal usage you can go down the common road and use `pip`:

::

    pip install orangebox

From source
~~~~~~~~~~~

::

    # fetch the source
    git clone <repository-url> orangebox

    # run install script
    cd orangebox
    python -m pip install .

Alternative install option for `development`_ is described here.

Code example
^^^^^^^^^^^^

.. literalinclude:: ../example.py
    :language: python3

.. include:: development.rst

Reference
^^^^^^^^^

.. toctree::

    parser
    reader
    types
    scripts

* :ref:`genindex`
