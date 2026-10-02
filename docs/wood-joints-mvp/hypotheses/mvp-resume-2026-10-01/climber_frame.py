"""Run the existing frame CLI with a climber weight in pounds.

All remaining arguments pass through to both_corner_frame.py. Its existing
horizontal scaling options, force laws, source pins and output gates apply.
"""

import argparse
import math
import runpy
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--climber-weight-lb", type=float, default=250.0,
                        help="positive climber weight; default 250 lb with the existing 2x live load")
    args, remaining = parser.parse_known_args()
    if not math.isfinite(args.climber_weight_lb) or args.climber_weight_lb <= 0:
        parser.error("--climber-weight-lb must be finite and positive")
    if any(arg == "--climber-load-scale" or arg.startswith("--climber-load-scale=")
           for arg in remaining):
        parser.error("use --climber-weight-lb instead of --climber-load-scale in this entry point")
    producer = Path(__file__).with_name("both_corner_frame.py")
    sys.argv = [str(producer), "--climber-load-scale", str(args.climber_weight_lb / 250),
                *remaining]
    runpy.run_path(str(producer), run_name="__main__")


if __name__ == "__main__":
    main()
