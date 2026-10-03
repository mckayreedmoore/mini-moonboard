# Testing review

## Result

No current force, owner, channel, moment, or balance mismatch was found in the
retained-frame report. This review covers only conditional demand and audit
reconciliation; it establishes no joint capacity or acceptance.

The reviewed producer is SHA-256
`af0a9569da228a8858f23107c16c7c8b3d9e0dbb50769733b5a399743eea6e24`; its
report is SHA-256
`f068cd5afc93c2b7027624b1fbec94ccb419f664833d920d2959f79bed661cc1`. All 143
report input pins matched the current source bytes. The report and producer
agree on 12 retained axes, 24 receiver memberships, 92 separate candidate
axes, 21 states, 252 bolt states, 504 endpoint wrenches, and 168 body states.
Each case reports 568 boundary interfaces and 720 source scalar ports.

## Checks performed

The parent run passed all eight producer tests and the targeted rerun for the
504 endpoint census. The tests enforce the 568-interface count in every state
and the 720-source-port count in each case; producer construction checks the
exact boundary names and source mappings. The refusal tests cover missing and
duplicate axes, missing receivers, a missing projection row, a wrong owner,
failed source law, wrong element, duplicate scalar, and changed source bytes.

I independently replayed `raw_oracle.py` against the canonical report. The
oracle passed with 756 raw-token channels (504 SPRING2 and 252 SPRINGA), 504
combined endpoint wrenches, and 168 authenticated receiver-datum instances.
It checks signed forces and rounding radii against DAT tokens, source owner and
channel identity against the pinned model and projection, and reporting-origin
moments and radii. All acceptance and fabrication flags remain false.

Four isolated report mutations were rejected for the intended reason: reversing
a retained scalar force, changing its receiver owner, removing a scalar
channel, and adding 10 Nmm to an endpoint origin moment. A forged freeze hash in
the report's `input_pins` was also rejected. The final oracle pins the freeze
bytes to SHA-256
`d4ba1c78eb358d25e32819201e9c59e05d425a06d9e4e5cca3dc09d7139ffd73`; its final
file hash is `9d04a698227d42207533e23b33afa08b7031518d8c80499251cdf4d4e791e758`.

I recomputed each body's external force and moment from the frozen model's
`physical_body_loads` and node coordinates, before support elimination, at the
all-body audit's original reference. All 168 references matched exactly, and
the maximum component difference for those force and moment sums was zero.
All 168 original-reference raw and interval balance gates pass under 0.1 N and
2 Nmm. I separately recomputed each body's origin moment radius from its
interface points and force radii; the maximum component difference was zero.
All origin-balance gate flags are false. The origin radius is descriptive and
does not inherit the original-reference 2 Nmm gate.

## Coverage boundary

The raw-token oracle independently checks the twelve retained axes. It does not
reparse all 568 boundary interfaces or all 720 scalar ports; the producer and
tests cover their source inventory and per-state interface census. The current
tests also do not mutate every individual source gate, or assert an expected
origin-radius vector in the small endpoint fixture. These are optional
regression additions: report construction checks the full source gate tuple,
and the raw oracle plus the independent recomputation above cover the produced
retained endpoint and body-origin radii.

The initial oracle review found that the freeze file's digest was not pinned
inside the oracle. The final version adds the fixed digest check and requires
the same digest in the report input pins; the forged-pin refusal check passes.
No native solve, CAD operation, or Git mutation was made for this review.
