# Independent review: upper washer-seat eccentric geometry

Reviewed on 2026-10-01 against these final bytes:

- `check_support.py`: `b9dd40be82d309da0ab1c61f4a277cc71e5bbbbc11ffc444bbfedee3e8a9fe57`
- `README.md`: `4a28bf7d13f4175e0019feae686496ea38e8236d2e557d24acd633b19b7fb3a6`
- Parent raw report: `62385f3e947f94fd5682f2b15a76d401bcceb5b6cff6a8fd18e7a4946dae1e0e`

The parent full run returned `PASS_CONDITIONAL_GEOMETRY_ONLY` for 32 axes, 64
unique outer seats, and 15 imported finished members. The saved report contains
six primary exclusions, 32 upper axes, and 54 remaining exclusions; all three
groups are disjoint and cover the 92 candidate axes. All 64 upper seats record a
3.75 mm bore radius. The maximum datum-plane offset is `1.0034e-9 mm`.

I inspected the source partition, seat-endpoint derivation, STEP authentication,
and the continuous swept-envelope argument. The code checks the frozen upper
review JSON hashes and the pinned model, hardware, bundle, and prior-method
sources. For each referenced member it verifies the model-to-manifest path and
hash, imports one valid solid, and compares its face count and volume with the
manifest. Each washer datum comes from the first or last receiver interval, and
the recorded bore must be present on the matching source STEP solid.

For each seat, the combined offset is the sum of the modeled bore/body radial
clearance and washer-ID/body radial clearance. Every translated washer
footprint outside its centered receiver bore lies inside the annulus from the
bore radius to the maximum OD radius plus that offset. The BREP Boolean tests
that whole annulus, so the containment result addresses every in-plane
translation direction. The four compass samples only compare the circle-area
formula against direct STEP measurements; they are not used as a global bound.
The outward disk check and both inward/outward checks are limited to depths
0.01, 0.05, and 0.1 mm.

The saved report has no geometry exceptions. Its minimum swept inward support
fraction is `0.9999999933494677` against the `1e-7` fraction tolerance, and the
maximum outward overlap is zero. All 768 direct area comparisons are within
`2e-5 mm²`; the largest difference is `3.286893e-6 mm²`. I independently
replayed three seats, including the seat with the lowest reported swept support,
using three imported STEP solids. The 36 direct measurements matched the saved
report within `4.4e-10 mm²`; an independently coded circle-intersection formula
matched those measurements within `1.67e-6 mm²`. The swept and outward checks
also reproduced for all three seats.

The production-path fixture passed when run with:

```sh
uv run --no-sync python docs/wood-joints-mvp/hypotheses/upper-washer-eccentric-support-2026-10-01/check_support.py --oracle-fixture
```

It measured a known bored-face case within `4.8317e-13 mm²` and rejected a
corrupted error, an empty sample set, and a nonfinite error. The area-oracle
gate records per-seat sample failures and makes them affect the report status.

These are geometry-only results for a conditional 6.35 mm nominal smooth-body
scenario and the recorded washer dimensions. They do not bound a delivered or
minimum shank, seat-location tolerance, tilt, physical flatness, washer
thickness contact, or unrecorded cuts absent from the frozen BREP. The result
does not establish contact pressure, washer or wood resistance, bolt/nut
resistance, joint acceptance, or the six-case envelope. No actual part or wood
was inspected, and no native solve or physical work was performed.
