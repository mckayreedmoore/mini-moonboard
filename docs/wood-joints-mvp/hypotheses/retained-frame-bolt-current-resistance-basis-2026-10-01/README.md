# Current retained frame-bolt conditional resistance basis

This packet joins the twelve retained axes and 24 current finished receiver
memberships to all 21 authenticated simultaneous rear states. It supplies
component references and explicit refusals, with **all 47 criteria pending**.
No current joint resistance is adopted. No CAD or native solve was executed.

The accepted [load-path packet](../retained-frame-bolt-current-load-path-2026-10-01/README.md)
and its independent raw receipt are hard-pinned. The producer rechecks their
143 input files and 19 additional method/source files. It computes bearing
lengths from current finished bore intervals and takes signed forces separately
on each receiver; proposed stock grain directions remain modeled assumptions.

The historical [WJ24 audit](../../wj24-retained-frame-bolt-audit.md) records
geometry, hardware policy and dimensional sensitivities. It has no current
signed joint resistance. Its old receiving distances and capacity claims are
not transferred here. The current receiver stacks independently give 177.8,
76.2 and 88.9 mm grips. Inherited maximum head-washer thicknesses yield
conditional body-to-transition thresholds of 158.9278, 69.3166 and 78.8416 mm.
These thresholds are dimensional screens requiring measured occupancy in each
member; catalog minimum thread lengths do not guarantee delivered shank.

The lateral scenarios assume full nominal D throughout both bearing intervals,
zero gap and DF-L G=0.5. They use the maintained six-mode numerical helpers,
direction-specific Hankinson bearing and 2024 reduction terms. Pure component
arithmetic does not satisfy the public method's finished-geometry/product
qualification gates. Main/side reversal preserves the minimum reference.
Generic 45 ksi from Appendix I.4 and the approximate Grade 5 106 ksi estimate
are illustrative Fyb scenarios; neither is adopted or test-derived product Fyb.

| Stack | Controlling current state and axis | Same-state lateral / axial tie (N) | 45 ksi reference (N), V/Z | 106 ksi reference (N), V/Z |
| --- | --- | ---: | ---: | ---: |
| Upper | A12 rear, factor 1, lumber_leg_bolt_left_2 | 1723.082 / 529.439 | 2307.661, 0.746679, IV | 3228.889, 0.533645, IIIm |
| Front | A12 rear, factor 1, rail_front_bolt_left_2 | 405.960 / 63.817 | 1130.126, 0.359216, II | 1130.126, 0.359216, II |
| Rear | A12 rear, factor 1, rail_rear_bolt_left_2 | 86.1565 / 14.9208 | 1221.882, 0.0705113, II | 1221.882, 0.0705113, II |

V/Z divides demand by an unadjusted, unqualified single-fastener reference.
Adjusted capacity and utilization remain `null`, as do Cg, Cdelta and the
service adjustment factors. These numbers do not dispose any criterion.

Every one of the 126 two-bolt group states has a resultant oblique to its row.
The existing Eq. 11.3-1 implementation requires a load-aligned row, so it
cannot supply Cg. Individual nonuniform bolt actions are preserved; the
resultant does not imply equal sharing. The directional geometry helper
locates loaded grain ends and cross-grain edges only in the proposed stock
box. Current trim/arc/multi-loop data exist, but no verified offline ray method
is bound to those finished faces while excluding the own bore. CAD-dependent
historical helpers were not run. Finished distances, Chapter 12 detailing,
Cdelta, splitting, group tear-out and cut-sensitive complete joints remain open.
The historical 2018 Commentary grain-angle interpolation is not adopted as
authenticated 2024 detailing.

The [Portland Bolt chart](https://www.portlandbolt.com/technical/thread-pitch-chart/)
provides nominal tensile stress areas of 0.1419 in² for 1/2-13 and 0.0775 in²
for 3/8-16. These are not measured minimum root areas. The
[Grade 5 supplier sheet](https://www.valuefastener.com/documents/products/capscrewgr5-8.pdf)
supports the conditional 92 ksi yield scenario. Nominal-area tensile first-yield
references are 58,070.644 and 31,715.820 N. Hypothetical full-D smooth-shank
shear first-yield references are 46,392.044 and 26,095.525 N. Same-state,
same-section average-stress von Mises ratios peak at 0.037722, 0.015621 and
0.003318 for upper/front/rear. This comparison excludes bolt bending, actual
threads and concentrations. It does not combine a threaded tensile stress
area with a shank shear area into an interaction: both interaction stresses
use the one hypothetical full-D interface section.

Actual product/grade, full-body transition, roots/class, steel areas, engagement,
washer resistance/contact, complete axial transfer and bolt bending remain
`null`. Force translation to a reporting datum is not bolt bending. No preload,
friction, floor rating, physical inspection or receiving conformance is credited.
The remaining three load cases are outside the authenticated source set.

Sources and locators are in [source-evidence.json](source-evidence.json), with
raw-byte hashes in [source-pins.json](source-pins.json). Supplier catalog pages
were checked directly; their raw HTML downloads were refused. The authored
source record captures only the bounded specification fields. Primary online
sources support catalog/material scenarios; delivered hardware and wood
cannot be established online.

Reproduce the report and run the focused checks from the repository root:

```sh
.venv/bin/python docs/wood-joints-mvp/hypotheses/retained-frame-bolt-current-resistance-basis-2026-10-01/produce.py --load-report /tmp/mini-moonboard-retained-frame-bolt-current-load-path-2026-10-01.json --raw-receipt /tmp/mini-moonboard-retained-frame-bolt-current-load-path-2026-10-01-raw-oracle.json --output /tmp/mini-moonboard-retained-frame-bolt-current-resistance-basis-2026-10-01.json
.venv/bin/python -m unittest discover -s docs/wood-joints-mvp/hypotheses/retained-frame-bolt-current-resistance-basis-2026-10-01 -p 'test_*.py' -v
.venv/bin/ruff check docs/wood-joints-mvp/hypotheses/retained-frame-bolt-current-resistance-basis-2026-10-01
```

The [validation receipt](validation.md) records independent arithmetic, raw
force checks, mutation refusal, deterministic replay and final reviews.
