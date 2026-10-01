# Independent review: primary-corner outer washer seats

Reviewed the frozen checker and README on 2026-10-01. SHA-256 at review:

- `check_support.py`: `9b3b773c2f7f1a51d5b5f9902ff288644133f67f63575a7c3a37168028e0dc57`
- `README.md`: `fc6e1c62fc712866554f85d8e90a8779e84e2ef635581e97e8130383218d7db6`

From the repository root, both commands passed against these checker bytes:

```sh
uv run --no-sync python docs/wood-joints-mvp/hypotheses/corner-washer-support-2026-10-01/check_support.py --self-test
uv run --no-sync python docs/wood-joints-mvp/hypotheses/corner-washer-support-2026-10-01/check_support.py --check
```

The self-test rejected neighboring-bore and wood-edge clipping, an embedded
seat datum, a reversed seat role, and an outward protruding boss. The boss
fixture retained full inward support and specifically reached the outward
overlap guard. The replay returned 36 checks: twelve outer seats on six bolts,
each tested with the CAD annulus and two independent catalog dimensional
extremes. At all three probe depths (0.01, 0.05, and 0.1 mm), minimum and
maximum inward support were 1.0, maximum outward overlap was 0.0, and maximum
unsupported area was 0 mm². Seat planes had at most `2.274e-13 mm` offset and
minimum absolute normal alignment 1.0. The reported kernel versions were
CadQuery 2.8.0 and OCP 7.9.3.1.

I confirmed the checker pins and reports the source JSON, source implementation,
CAD dimension, hardware, and bundle hashes; it also verifies the four actual
STEP hashes against the model binding and bundle manifest before import. Each
imported BREP is one valid solid and matches its recorded face count and
volume. The candidate and revision are checked explicitly. BG003 is checked
as a three-receiver stack in the pinned order (`knee_outer_left_spine`,
`base_side_left`, `knee_outer_left_inner_frame_block`), with the source
no-middle-axial-washer-seat flag true and only the two endpoint washer seats.
The seat owners, coordinates, and source-proposed grain directions are also
cross-checked.

This verifies annular footprint support in the four frozen source solids only.
The probe centers each annulus on the modeled bolt axis; washer eccentricity,
lateral movement, and seat-location tolerances are not varied. The source
bundle has no semantic cut inventory, so cuts absent from the frozen BREP are
not independently reconciled. The result does not establish selected or
delivered hardware, actual fit, flatness, contact pressure, washer or bolt
resistance, wood resistance, load transfer, joint acceptance, or the six-case
envelope. No native solve or geometry change was part of this review.

Remaining inputs for conditional washer-stack load-transfer work are bounded
cap-head and nut bearing-face/chamfer geometries, washer geometry, and the
coupled action/contact assumptions. The README correctly allows declared,
supported scenarios before product selection or receiving. Stronger claims
about a particular product or built joint still need part-specific or observed
evidence, including the physical wood-face condition; the support check itself
does not create that evidence.
