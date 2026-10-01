# Independent source-coordinate and action review

October 1, 2026. I found no source-join or arithmetic discrepancy in the
bounded placement and interface-action packet. This review checks modeled
source geometry and forces. It does not accept an NDS row/group, adopt a
factor, establish member resistance, or accept the joint.

The independent verifier is `parent_verify.py`, SHA-256
`a43dae9081674a9dd043da5f5da1157e1fa3da9d04567994697a869437e314b7`. It
binds producer `75e7eed05e9f24c1a04b35a8faeb03e4f284259ae2af54abd45c611bb2e0684f`,
placement report `21c2eba56b80efa174cdb5ecdb206468a6b15882732c6edd548d2027063f58c3`,
the prior bottom-joint source `fcf393be26c433daf760a6afcf9fd6260d88f04f43a6234def960bbba4789029`,
feature register `bebb4274cdecfb6ad0b0f26850d85a16570c245ea9f7d478c0b05c12b4513e19`,
and the frozen case manifest. It rehashes the original model, native response,
all-body audit, source methods, and each referenced finished STEP.

I derived the eight receiver placements independently from the current
`axis-features.json` rows. For each receiver, the global axis datum and
direction were projected into the recorded stock-frame basis and compared to
the feature-register g/q/r datum. I then derived the transverse edge direction
from grain × bolt axis, the distances to the proposed stock bounds, and the
matched radius-3.75-mm bore interval. The output's 6.35-mm value is the
modeled occupied-diameter scenario; this calculation does not identify a
delivered bolt, drilled hole, lumber datum, or shop measurement.

The 96 saved ray rows have the expected eight placements × three stations ×
four directions. I independently checked each station point, direction,
interval list, void complement, terminal flag, and projected stock-bound
distance. The analytic cross-grain check reproduces all 48 `e±` endpoints at
the proposed stock side planes. Thirty-six of the 48 grain-direction endpoints
match their stock-coordinate distances. The other 12 are the two `g` rays at
three stations for each of the two `base_side_left` receiver memberships;
their saved rays stop at finished cuts before the stock-envelope ends, and
the report correctly leaves `continuous_depth_extrema_proved` false. I did
not treat the discrete rays as a continuous-depth extremum proof. The separate
finished-edge review owns the detailed face and cut identification.

For forces, I compared each saved bottom-joint action with the same named
action in the original frozen response before doing the arithmetic. For all
168 member/bolt states, I selected force and point from the action's actual
first or second endpoint, projected the signed lateral vector and its
componentwise radius into that member's stock basis, and kept the axial tie
separate. I independently recomputed the grain and edge component interval
signs, candidate loaded-edge direction, full bolt vector, and angle to the
bolt axis. This preserves native sign and rounding evidence while keeping
the candidate edge label a vector diagnostic only.

For all 84 member/interface rows, I reconstructed the eight-action sums from
the frozen response: two lateral planes, two separate outer-seat ties, and
four contact cells. For each action I used the member-side force and its
corresponding `first_point` or `second_point` when present; this retains the
different tie endpoints. I then summed force/radius vectors and transported
each moment to the midpoint of the two source axis datums. The reconstructed
records match the published interface vectors, moments, radii, and pair-line
angles. The maximum interface force resultant is `542.1915355737689 N`; the
maximum reported midpoint moment resultant is `23290.872504896564 Nmm`. These
are sums for the named two-member interface only: they exclude other
interfaces and body loads and do not form a complete member free body.

The full-load interface angles in the README also reproduce: rail/side are
`23.221108° / 80.279624°` for A1 rear, `67.771060° / 47.570232°` for A12
rear, and `69.466933° / 70.459323°` for K12 rear. The eight-action direction
diagnostic does not determine whether a complete connection qualifies for an
NDS row or group factor. The report correctly leaves `Cg`, `CΔ`, the
Table 12.5.1C pass, and joint acceptance unadopted/false.

The full deterministic producer replay used the exact source
`/tmp/mini-moonboard-bottom-outer-joint-2026-10-01.json` under the repository
`.venv`. Replay output at
`/tmp/mini-moonboard-bottom-outer-placement-2026-10-01-replay.json` is
byte-identical to the pinned placement report (SHA-256
`21c2eba56b80efa174cdb5ecdb206468a6b15882732c6edd548d2027063f58c3`). The
independent verifier returned
`PASS_INDEPENDENT_SOURCE_COORDINATE_AND_INTERFACE_WRENCH_ORACLE`, and Ruff
passes on the verifier. Reproduce it from the repository root with:

```sh
.venv/bin/python docs/wood-joints-mvp/hypotheses/bottom-outer-bolt-placement-2026-10-01/parent_verify.py
```

No native solve, geometry change, or hardware selection was made for this
review. The saved geometry and force results remain conditional model inputs,
not observations or strength acceptance.
