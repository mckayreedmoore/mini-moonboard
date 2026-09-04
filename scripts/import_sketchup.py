"""CLI wrapper: ``uv run python scripts/import_sketchup.py source.skp output.obj``."""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))
from mini_moonboard.sketchup import export_skp_obj


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract a SketchUp reference model to millimetre OBJ")
    parser.add_argument("input", type=Path, help="SketchUp .skp input")
    parser.add_argument("output", type=Path, help="OBJ output")
    args = parser.parse_args()
    print(export_skp_obj(args.input, args.output))


if __name__ == "__main__":
    main()
