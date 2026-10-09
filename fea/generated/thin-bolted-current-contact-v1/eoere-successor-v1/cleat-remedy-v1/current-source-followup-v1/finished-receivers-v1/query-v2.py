"""Reuse the frozen geometry adapter with a JSON-canonical inventory join.

The first adapter's toy methods passed, but its source intake compared tuple
profile vertices directly with JSON lists. Preserve those issued bytes and
replace only that private intake function; all native query methods stay exact.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
from pathlib import Path

OWN = Path(__file__).resolve()
LEGACY = OWN.with_name("query.py")
LEGACY_SHA = "b9a888032c19a7616619bb27355aa2aeb5a0ade862aa748ad08d80ababd0ebfb"


def load_adapter():
    if hashlib.sha256(LEGACY.read_bytes()).hexdigest() != LEGACY_SHA:
        raise ValueError("exact frozen v1 geometry adapter required")
    spec = importlib.util.spec_from_file_location("four_receiver_frozen_adapter", LEGACY)
    query = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(query)
    query.require(query.sha(LEGACY) == LEGACY_SHA, "frozen adapter changed during import")
    # Only this new private module instance is adapted; no source bytes change.
    query.OWN = OWN
    original_preflight = query.preflight

    def preflight(permit_path, fixtures_only):
        inp, pins, permit, runtime = original_preflight(permit_path, fixtures_only)
        path = str(LEGACY.relative_to(query.ROOT))
        query.require(path not in pins or pins[path] == LEGACY_SHA, "conflicting frozen adapter pin")
        pins[path] = LEGACY_SHA
        query.verify(pins)
        return inp, pins, permit, runtime

    def source_inventory(inp):
        analytic = query.module(inp["helpers"]["analytic_inventory"], "four_receiver_analytic_inventory_v2")
        bound_input = query.read(query.ROOT / inp["analytic_inputs"]["path"])
        data = {k: query.read(query.ROOT / ref["path"]) for k, ref in bound_input["sources"].items()
                if ref["path"].endswith(".json")}
        datum = query.module(bound_input["sources"]["datum_helper"], "four_receiver_datum_v2")
        axes, proposed, members, own_cuts = analytic.existing_inventory(bound_input, data, datum)
        prior = query.read(query.ROOT / inp["analytic_result"]["path"])
        query.require(query.canonical(members) == query.canonical(prior["affected_members"])
                      and query.canonical(list(proposed.values())) == query.canonical(prior["proposed_axes"]),
                      "analytic canonical source inventory differs")
        query.require(set(members) == set(inp["receivers"]) and set(proposed) == set(inp["axis_ids"]),
                      "exact four-host/axis scope required")
        return data["geometry"], axes, proposed, members, own_cuts

    query.preflight = preflight
    query.source_inventory = source_inventory
    original_main = query.main

    def main():
        # Preserve the requested directory entry before v1 normalizes it.
        # The original locked mkdir(exist_ok=False) still reserves new outputs.
        parser = argparse.ArgumentParser(add_help=False)
        parser.add_argument("--outdir", type=Path)
        args, _ = parser.parse_known_args()
        if args.outdir is not None:
            query.require(".." not in args.outdir.parts, "parent traversal output rejected")
            query.require(not args.outdir.is_symlink() and not args.outdir.exists(), "requested output entry already exists")
        return original_main()

    query.main = main
    return query


if __name__ == "__main__":
    load_adapter().main()
