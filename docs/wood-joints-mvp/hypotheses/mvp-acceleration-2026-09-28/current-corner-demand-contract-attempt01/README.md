# Complete left outer corner demand contract

This input-only contract identifies the five current corner bodies and every
source-owned internal, incoming or onward interface touching them. It uses
the frozen C11 **input** inventory; no C11 response or active states are used.
The 338 owned connection groups are a bookkeeping boundary, not 338 bolts.
Most represent contact cells or other routes touching the long side/header.

BG001/BG003/BG045 comprise six new physical bolts, eight lateral shear planes
and six outer-seat tension ties. The two BG003 continuous three-member bolts
each have two shear planes and one outer-seat tie. The whole model has 92 new
block axes and twelve separate original LEG/FLOOR-RUNNER axes. Their unchanged
resistance evidence is not reopened here.

`contract.json` records source points, physical owners and the results needed
from a valid response. Preserve separate outer-seat points when computing
moments. Reporting only the three bolt-group sums would omit parallel member
bearing and onward transfer. Each of the five bodies must close under its
loads and all incident interface forces before a complete corner result can
be used.

Reproduce with `uv run --no-sync python3 produce.py`. No native solve, new
geometry, force result, adjusted resistance or joint acceptance is produced.
