# Rotated orthotropic stress-output preparation

This is an unfrozen, unexecuted hypothetical method fixture. All 47 criteria
remain pending. No solver, CAD, mesh generation or native-ledger operation is
performed by its producer.

The pinned CalculiX 2.23 HTML manual defines `*EL PRINT` stress output as local
by default (`GLOBAL=NO`). An applied `*ORIENTATION` supplies that frame; explicit
`GLOBAL=YES` requests global components. Local rows append the first ten
characters of the orientation name. The authoritative archive is
`/tmp/ccx_2.23.htm.tar.bz2`; relevant members and SHA-256 hashes are:

| Member under `./CalculiX/ccx_2.23/doc/ccx/` | SHA-256 |
| --- | --- |
| `node280.html`, EL PRINT | `205d49398f5dc3e821b4032bdf8425725484cf5eda4f9fcdd15956e0d50f1544` |
| `node330.html`, ORIENTATION | `c6dd3154d3bbebfe144aab6b36694c9037f611d5db09d5a0fb968486b06ce2d9` |
| `node274.html`, ELASTIC | `8c34b9f16d20d93ff0723bc529337c2b84cd60b8973c13ae08c99ae557b5d818` |

The existing rotated matrix coupon prints no stress; the completed affine
annulus has no orientation. This fixture reuses only the latter's authenticated
800-node, 384-element straight-sided C3D10 mesh and 512 boundary nodes. It
prescribes a nontrivial homogeneous global strain on every boundary DOF and
applies a constant rotated reciprocal orthotropic tensor. Its expected global
and local stresses differ, making a frame mix-up observable. Three separate
element-set aliases request explicit global, explicit local and default output
within one linear step. Whether that output selection behaves as documented
is part of the future known-answer check.

`prepare.py --output-directory /tmp/NEW_EMPTY_DIRECTORY` creates a separate
unfrozen deck and analytical expectation file. Existing inputs stay unchanged.
It emits 1,536 boundary constraints and keeps 864 interior DOFs free. The
stress and energy expectations come from the separate parent analytical
oracle, not observed native results.

The pure `check_output.py` reader checks every integration point in all three
sets, all 800 displacement rows, orientation suffixes, census, time and total
energy. Its predeclared numerical tolerances are stress absolute `1e-6 MPa`
or relative `1e-5`, displacement absolute `1e-9 mm` or relative `1e-6`, and
energy absolute `1e-10 N·mm` or relative `1e-5`. These allow the documented DAT
print precision; they do not qualify stress accuracy in a candidate contact
model. Seventeen pure tests pass, including deliberate output corruptions
and an independent reciprocal-compliance calculation. That calculation uses
the stated constants and 40-degree axes, solves the three normal equations by
Gaussian elimination, checks both stress tensors and their transformation,
and verifies local/global strain-energy equality. It does not import a solver
or use a source FE matrix.
The source producer created only an unfrozen deck and expectation file in
`/tmp/mini-moonboard-orthotropic-stress-frame-source-preparation-2026-10-01`.
Its deck SHA-256 is
`71bd77a1f8074aa4a5a4a72416140b0b5e64d8db1f39b7dc68da86063159db97`.

Independent source review, a parent wrapper binding raw output to the terminal
native execution and exact freeze, and native readiness remain unfinished.
The reader alone authenticates no execution or artifact provenance. A future single run
would use the existing 2.23 image under one CPU, 1 GiB and 60 seconds after
those controls are complete. No run is reserved or authorized here. This
method check supplies no wood property, washer resistance or joint capacity.
The current Docker socket denied even the primary's read-only image inspection;
no build or native execution can proceed under the present permissions.
