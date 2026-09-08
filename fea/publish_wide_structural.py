"""Archive wide-principal stiffness diagnostics, not connection qualification.

Run sequentially as a CLI: the reused publisher's temporary module settings are
restored even when validation fails. Historical publisher files remain unchanged.
"""
import argparse
from pathlib import Path

from fea import publish_timber_structural as publisher

KEY = "wide-principal-development"
OUTPUT = Path("fea/results/wide-principal")
PUBLISHER_SOURCES = (*publisher.PUBLISHER_SOURCES, "fea/publish_wide_structural.py")


def publish(results):
    previous = publisher.KEY, publisher.OUTPUT, publisher.PUBLISHER_SOURCES
    try:
        publisher.KEY, publisher.OUTPUT, publisher.PUBLISHER_SOURCES = KEY, OUTPUT, PUBLISHER_SOURCES
        return publisher.publish(results)
    finally:
        publisher.KEY, publisher.OUTPUT, publisher.PUBLISHER_SOURCES = previous


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("results", type=Path, nargs=2)
    publish(parser.parse_args().results)
