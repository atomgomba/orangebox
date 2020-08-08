.. title:: Types

.. automodule:: orangebox.types

    Types module
    ------------

    Contains internal types used by the reading and parsing logic.

    .. toctree::
        :titlesonly:

    Frame
    ^^^^^

    A named tuple to hold frame data.

    .. autoclass:: Frame

    FrameType
    ^^^^^^^^^

    Enumerates the types of frames in a data stream.

    .. autoclass:: FrameType
        :members:

    FieldDef
    ^^^^^^^^^
    .. autoclass:: FieldDef
        :members:

    EventType
    ^^^^^^^^^

    Enumerates known log event types.

    .. autoclass:: EventType
        :members:

    Event
    ^^^^^^^^^

    A named tuple to hold event data.

    .. autoclass:: Event
