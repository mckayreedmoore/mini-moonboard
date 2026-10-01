# Independent radial-gap fixture sign audit

Status: **PASS for the frozen analytical inputs and branch signs; no native
solver was run.** This review checks the disconnected linear branches in this
method fixture only. It does not validate a current joint, a full-frame
active-set solve, or mechanical acceptance.

## Frozen inputs checked

The review is bound to these SHA-256 values:

| Artifact | SHA-256 |
| --- | --- |
| `model.inp` | `9ef7b11ecf4d3944f42fc2134a08bed58290ddcff91b6551321706b2b553cf44` |
| `expected_answers.json` | `e2dda49e8925888fa2fc22d360a66a2ab5ae80a8519612dade5fc9056d9a0af8` |
| `README.md` | `34a90733fd1f433b63ffebbb35dd6f2b1b631434aca49d61ea46d08608917ea7` |
| `preparation.json` | `f5a2be2284bb1c3f6bd319aafcfc09fd25cbbce67800c77c82dd0e77f2413812` |

The four values also match `SHA256SUMS`. The six source hashes recorded by
`preparation.json` match the live solver profile, response/state helper,
force-output helper, frame helper, prior active-branch deck, and RF-to-opening
deck at review time. No input, shared solver source, full-frame input, or c10
artifact was changed.

The boundary concern was checked against this same `model.inp` digest; no
other or stale deck was reviewed. The only `*BOUNDARY` block is at lines
218–239. First hosts 11, 21, 41, and 61 are fixed in DOFs 1–3 at lines 221,
223, 227, and 231. Open-branch anchors and first hosts 1, 31, and 51 are
likewise fixed in DOFs 1–3 at lines 219–220, 225–226, and 229–230. In
contrast, free second-host nodes 2, 12, 22, 32, 42, 52, and 62 are restrained
only in DOF 1 at lines 233–239. Thus the first-host radial reference CLOADs
act at prescribed DOFs and are carried by their support reactions; they do
not force the raw connector force to equal the reference term.

## Independent derivation

The fixture uses gap radius `c = 0.5 mm`, equal lateral contact component
stiffness `k = 2000 N/mm`, and a separate host support stiffness
`kh = 10000 N/mm` per radial axis. For a stored contact normal `n` and
relative host displacement `r = u_second - u_first`, the active linear branch
has raw force on the first endpoint `q = k r`. Its gap-reference force is
`q_ref = k c n`, so the physical contact force on the first endpoint is
`q_phys = k(r - c n)`. The paired host loads are `-q_ref` on the first host
and `+q_ref` on the second. In a one-axis active branch, host equilibrium is
`P_base + (-kh r) - q_phys = 0`; the deck adds `q_ref` to the second-host
CLOAD, so its active-branch displacement is
`r = (P_base + q_ref)/(kh + k)`.

| Branch | Independent result | Sign / state conclusion |
| --- | --- | --- |
| Open interior | `r=(0.18,0.24) mm`, `|r|=0.30<c`; host support returns `(-1800,-2400) N` against the applied `(1800,2400) N`. No contact spring is present, so radial force is zero. | Correct open state, including a non-axis-aligned point inside the circular gap. |
| Positive-side engagement | `r=0.75 mm`; `q=2000(0.75)=+1500 N`, `q_ref=+1000 N`, `q_phys=+500 N`. The receiver balance is `+8000-7500-500=0 N`. | Correct compression on the `+Y` side; the stored and proposed normals agree. |
| Positive-side unload probe | `r=0.30 mm`; `q=+600 N`, `q_ref=+1000 N`, so retaining the old branch would give `q_phys=-400 N`. The open state instead has zero contact force and host balance `+3000-3000=0 N`. | Correctly marks the old branch for release; the negative corrected force is diagnostic tension, not accepted bearing force. |
| Reversed displacement on old positive branch | `r=-0.75 mm` with stored `n=+Y`; `q=-1500 N`, `q_ref=+1000 N`, and the retained branch would give `q_phys=-2500 N`. Also `r·n=-0.75<c`. | Correctly releases the old side; it cannot carry the reversed displacement. |
| Open opposite-side transition probe | `r=-0.75 mm`, `|r|=0.75>c`; with no radial spring the radial force is zero and the open state proposes `r/|r|=-Y`. | Correct negative-side selection after release. This is an active-set transition probe outside the gap, not a final equilibrium state. |
| Negative-side engagement | `r=-0.75 mm`, `n=-Y`; `q=-1500 N`, `q_ref=-1000 N`, and `q_phys=-500 N`. The receiver balance is `-8000+7500+500=0 N`. | Correct compression on the `-Y` side after the open transition. |

The reference-load correction signs therefore agree on both sides. For the
positive branch, the second-host CLOAD is `8000+1000=9000 N`; for the
negative branch it is `-8000-1000=-9000 N`. Subtracting the signed reference
term after recovering the raw spring force gives `+500 N` and `-500 N`,
respectively. The correction loads are not physical contact demand.

For each active radial `SPRING2`, the recorded endpoint order gives
`q = k (U_second - U_first)`. Under the pinned CalculiX 2.23 output method,
`RF_first=-q` and `RF_second=+q`; therefore
`(RF_second-RF_first)/2 = q = k ΔU`, and endpoint action/reaction sums to
zero. The frozen expected endpoint pairs are consistent: element 1103 gives
`(-1500,+1500) N`, 1203 gives `(-600,+600) N`, 1403 gives
`(+1500,-1500) N`, and 1603 gives `(+1500,-1500) N`; each paired Z
component has zero displacement and force. Recover `q` from endpoint RF
first, then subtract `q_ref`; host CLOADs do not directly load the auxiliary
spring endpoint DOFs.

## Limits

The signs and arithmetic are internally consistent, including the fixed-host
boundary conditions. The packet models each
branch as a disconnected linear static problem with manually included or
omitted radial springs. The old-side unload/reversal and open opposite-side
cases are transition probes; the deck does not make CalculiX switch the
unilateral active set or demonstrate a continuous load-history solution.
The separate host springs stabilize these small probes and do not establish
stability of an all-open full-frame branch. The engaged displacement cases
are aligned with their stored normals, so this fixture does not qualify
off-axis/tangential bearing behavior or friction.

The expected answers pass independent input-level derivation. Their printed
U/RF interval checks still require a later native result and must not be
described as passed before that result is audited.
