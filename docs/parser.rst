.. title:: Parser

.. automodule:: orangebox.parser

    Parser class
    ------------

    The main class for getting decoded frames from blackbox log files. It also builds the field definitions from the raw headers.

    .. autoclass:: Parser
        :members: events, headers, field_names, reader

    Factory
    ^^^^^^^

    To create a new instance use the static factory method:

    ::

        # load the second session from a flash chip log
        parser = Parser.load("btfl_all.bll", 2)

    .. automethod:: Parser.load

    Read data
    ^^^^^^^^^

    ::

        # select the 3rd session
        parser.set_log_index(3)

        # print field values frame by frame
        for i, frame in enumerate(parser.frames()):
            print("frame #{:d}: {!r}".format(i, frame))

    .. automethod:: Parser.frames
    .. automethod:: Parser.set_log_index
