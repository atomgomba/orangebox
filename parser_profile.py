import cProfile
import io
import logging
import pstats
from pstats import SortKey

from parser_benchmark import main

if __name__ == "__main__":
    # disable logging, but it doesn't seem to be a big performance hit anyway
    logging.disable(logging.CRITICAL)

    pr = cProfile.Profile()
    pr.enable()
    main()
    pr.disable()

    outs = io.StringIO()
    ps = pstats.Stats(pr, stream=outs).sort_stats(SortKey.CUMULATIVE)
    ps.print_stats()
    print(outs.getvalue())
