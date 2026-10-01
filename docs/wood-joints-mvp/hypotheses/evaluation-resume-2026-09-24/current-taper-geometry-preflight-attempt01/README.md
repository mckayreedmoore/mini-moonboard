# Current-CAD taper geometry preflight — attempt01

This input-only packet authenticates `compact-floor-flush-wood-joints-development` revision `led-clearance-2x6-runner-seated-blocks-v1`.
Both current leg STEP BReps have a measured 457.2 mm run, 38.1 mm recess,
12:1 run/depth ratio, and 88.9 × 139.7 mm intended section. The two exact
adopted geometry predicates pass on these CAD inputs. **Both full criteria
remain pending:** their adopted table requires FR-3 and a fresh current case.

The producer verifies 216 source and implementation pins,
including the 50-member bundle, all 50 STEP hashes, the current candidate,
the longitudinal-axis map, the stock records and exact adopted predicate/text.
It imports only the two current leg STEP solids with CadQuery 2.8.0 and OCP
7.9.3.1.1. Taper selection uses plane orientation, never a face ordinal or a
nominal 12:1 slope. Four straight edges, the four corners, plane normal, area,
cross-grain extent and full-stock return independently constrain each result.
The geometric face record is hashed. Length consistency uses 1e-5 mm; area
uses 1e-3 mm²; the adopted predicates retain their own exact source tolerances.

This closes the missing current-CAD taper dimension input. It does not prove
native/CAD equivalence, mesh volume, section coverage, unbored torsion method
applicability, stock receipt, joint mechanics, resistance or acceptance. It
imports no historical result. All release and engineering completion flags
remain false. Fresh native geometry/case authentication and an independently
reviewed criterion binding remain required.

From the repository root:

```sh
.venv/bin/python -B scripts/build_current_taper_geometry_preflight_attempt01.py --check
.venv/bin/python -B -m pytest -q -p no:cacheprovider tests/test_current_taper_geometry_preflight_attempt01.py
.venv/bin/ruff check --no-cache scripts/build_current_taper_geometry_preflight_attempt01.py tests/test_current_taper_geometry_preflight_attempt01.py
```

From this packet directory, `sha256sum -c SHA256SUMS` verifies its local files.
`--write` creates the packet once and refuses an existing directory. `--check`
authenticates the pinned inputs, remeasures both exact BReps and compares every
report, verification, source-pin, README and checksum byte. No solver or
geometry export is invoked.
