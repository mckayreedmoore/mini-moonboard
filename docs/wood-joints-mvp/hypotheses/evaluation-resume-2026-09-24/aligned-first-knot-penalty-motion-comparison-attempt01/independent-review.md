# Independent review of the first-knot comparison

I independently checked the two immutable first-knot snapshots, all 339 rows in each `PILOT_MONITOR` block, the pinned source inputs, the `compare.py` implementation pin, and the native energy records. No native solve or CAD operation was run.

Both snapshots contain one accepted increment from 0 to 0.001 s on attempt 1 (25 iterations for K=100000, 26 for K=10000). The snapshot and every result-file hash match their records. Each complete monitor block has 339 unique, finite rows: 331 loaded nodes and the eight nut reference/rotation controls. The two freezes carry identical loaded-node unit-force weights and controller IDs.

The controller components are correctly interpreted as rotations. The pinned [rigid-carrier input](../ordinary-transient-seating-100n-aligned-attempt01/rigid-carriers.inp) has SHA-256 `a15eebb0537a4a3f096531f2c4e48ecd26b6ec53908d61178ead7dfe3bc27815` and declares ROT NODEs 116164, 116166, 116168 and 116170. That exact set matches both freezes' `rotation_nodes` and is present in both monitor blocks. The local CalculiX 2.21 manual, SHA-256 `16b6bab5a3f1a40a21fff62379f95c804a58d93758ab2e9a489b18d911dc20c8`, section 7.112, specifies that a dummy ROT NODE's translational DOFs 1–3 represent rotations about the reference node's global X/Y/Z axes and can be printed with `*NODE PRINT`. The values at these four declared dummy nodes are therefore angular coordinates in radians; the ordinary physical-node displacement rows remain millimetres.

Independent signed-field recomputation matches [the comparison report](report.json):

| Field | Baseline reference infinity norm | Absolute infinity difference | Normalized difference | Contract screen |
| --- | ---: | ---: | ---: | --- |
| q | 2.3186867121e-5 mm | 9.7258232512e-7 mm | 4.1945% | Within 5% |
| Loaded U, 331 nodes × 3 components | 1.352211e-5 mm | 2.014678e-6 mm at (9,1) | 14.8991% | Flagged above 5% |
| ROT NODE U1–U3, 4 nodes × 3 angular components | 5.012359e-8 rad | 1.195379e-8 rad at (116168,3) | 23.8486% | Flagged above 10% |

The report's separate maximum vector magnitudes also match the monitor rows: loaded-node displacement is 1.8515880223e-5 mm (baseline) and 1.9882482444e-5 mm (child); controller rotation is 6.6438947950e-8 rad and 5.6713459780e-8 rad. The componentwise infinity-field comparisons, rather than these maxima, govern the contract screens.

The frozen run input maps have the same `pilot.inp` hash, `48649259ba8441429a5dd094ae08487e3713d6b5b860ac39ca1acf71b837d963`. I parsed its 662 CLOAD entries against the frozen unit field: every component is scaled by 100, and the first RAMP_N knot is 0.000298 at 0.001 s, giving a scalar pattern-force coefficient of 0.0298 N. Thus the first-increment work formula in `compare.py` is numerically correct for both captured runs. Among common solver-deck artifacts, the only changed file is `contact-fragment.inc`; its sole numerical card change is the linear contact penalty from 100000 to 10000 N/mm³. `contact-manifest.json` also differs as accompanying metadata but is not included by the solver deck.

Using q from each monitor block, the reconstructed zero-to-first-knot work is `0.5 × 0.0298 × q`: 3.4548432010e-7 N·mm for the baseline and 3.5997579675e-7 N·mm for the child. Native external-work prints are 3.454843e-7 and 3.599758e-7 N·mm, respectively; both agree to printed precision. This discrete-work agreement does not close the native energy balance. Internal and kinetic energy changes are 3.2885% and 4.2833%, below their declared 10% screens. The native relative energy discrepancy increases from 1.230541% to 3.905511% (2.67497 percentage points), which is flagged by the declared screen. Penalty energy is 1.3258% and 3.9117% of the stated mechanical-energy sum, both below the separate 5% screen.

The earlier amplitude/load reproducibility gap is closed in the current [`compare.py`](compare.py). It verifies each `pilot.inp` against its freeze, parses the full CLOAD field against the frozen unit weights, checks the common scaling, reads RAMP_N and derives the first-knot force coefficient, then requires identical load evidence for both branches. The report records 662 CLOAD components, scale 100, first-knot amplitude 0.000298 and coefficient 0.0298 N. This matches my independent parse of the pinned decks. The numerical flags remain unchanged. These are first-knot transient numerical screens only, not a settled response, capacity result or mechanical acceptance.

The report binds comparison implementation SHA-256 `181a98ffb61f24694c4e5567ef514f34073c654259c10a69d84310288199b796`, contract SHA-256 `0d854a2d3d75bd395b00eae3c5b563a00e595b9b38da63d4ceb3d8c637ffd9b7`, and both snapshot SHA-256 values. The final [report.json](report.json) SHA-256 is `cc81f806f7f11286d3c7f46614813ef1c11c088ee328dd0ef520cda83dc7018f`.
