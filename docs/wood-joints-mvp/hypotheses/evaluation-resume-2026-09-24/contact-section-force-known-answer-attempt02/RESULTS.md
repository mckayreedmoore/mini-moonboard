# Section and stress output fixture result

**PASS — the small output-method fixture.** Both separate CalculiX 2.23
cases pass the unchanged mechanical and section-force gates. Adding only
`*EL FILE,FREQUENCY=1 / S` restores complete nodal FRD output. The failed
attempt01 remains preserved; no joint response or structural criterion is
accepted through this result.

Both cases completed normally in about 0.32 seconds each, with exit zero,
no OOM, three accepted endpoints and three iterations per endpoint. The
MORTAR iteration cap of 14 was not reached. All frozen input and native output
hashes match. The parent reran the frozen verifier, which reports
`PASS_SECTION_STRESS_FIXTURE`.

At each endpoint, `DISP`, `FORC` and `STRESS` contain all 54 model nodes.
Each stress record has six finite components. Contact fields are finite;
their coverage is nine nodes for MORTAR and 54 for penalty. These field counts
are output diagnostics, not equivalent contact-force representations. The
incidental `ERROR` field is recorded without a stress-error acceptance claim.

The DAT displacement/reaction arrays and STA/CVG row tokens exactly match the
passing full-step baseline. This is nodal-array parity; the complete DAT file
also contains the additional SOF reports. The [independent raw-output review](independent-review.md)
confirms source/output hashes and complete finite nodal coverage. All six SOF reports per case pass the force,
moment, area, centroid and normal checks. Compression results are:

| Quantity | MORTAR | Penalty |
| --- | ---: | ---: |
| Top reaction magnitude (N) | 399.519883391 | 399.519899999 |
| Section-force magnitude (N) | 399.5159 | 399.5159 |
| Pressure compliance (mm³/N) | 0.000050060086698 | 0.000050060084617 |

The frozen force reference remains 400 N and the section-vector error limit
remains 4.001 N. The approximately 0.4841 N section error passes that limit.
Opening and reopening remain below the original 0.001 N force limit.

The result supports the pinned-source output diagnosis: stress extrapolation
after contact output restores the node-activity array used for FRD selection.
See the [failed result](../contact-section-force-known-answer-attempt01/RESULTS.md)
and [pre-execution wording clarification](documentation-clarification.md).
Attempt01 requested no stress field; its failure was missing nodal output.

This qualifies this output combination on this fixture and schedule. SOF
remains a bulk-stress integration proxy; nodal stress is not pair-local
contact traction or capacity. The next joint-method gate is the separate
shared-boundary contact fixture, followed by an applicable action and energy
output contract. Its inputs and checks must be reviewed on their own terms.

| Evidence | SHA-256 |
| --- | --- |
| Input freeze | `0603288af8a4385000d029eca0e31bda57fc63f39e474796033213026b5aa8f7` |
| Execution | `2736908e0f59c73a43330021c6c3798e46fc3726b22a179ec3dcb1ee07b43435` |
| Verifier source | `c68a9fd998d8ed601d4223118af1699b343cc6688e37818e03131fd84321524b` |
| Passing audit | `4a0fe723f21686ffa6e0d41ca7724b5f901b6234db87a4ac7b3a376dd73da215` |

The [execution record](execution.json) binds the exact unpatched image,
executable, per-case terminal states and every native output hash. The
[parent review](parent-review.json) records pre-run readiness. Geometry,
criteria and all release flags remain unchanged.
