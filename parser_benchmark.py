import logging
import sys
import timeit

from orangebox import Parser

number_of_runs = 1


def main():
    parser = Parser.load(sys.argv[1])
    list(parser.frames())


if __name__ == "__main__":
    # disable logging, but it doesn't seem to be a big performance hit anyway
    logging.disable(logging.CRITICAL)

    print(timeit.timeit(main, number=number_of_runs))
