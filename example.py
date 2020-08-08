from orangebox import Parser

# Load a file
parser = Parser.load("btfl_all.bbl")
# or optionally select a log by index (1 is the default)
# parser = Parser.load("btfl_all.bbl", 1)

# Print headers
print("headers:", parser.headers)

# Print the names of fields
print("field names:", parser.field_names)

# Select a specific log within the file by index
print("log count:", parser.reader.log_count)
parser.set_log_index(2)

# Print field values frame by frame
for frame in parser.frames():
    print("first frame:", frame.data)
    break

# Complete list of events only available once all frames have been parsed
print("events:", parser.events)

# Selecting another log changes the header and frame data produced by the Parser
# and also clears any previous results and state
parser.set_log_index(1)
