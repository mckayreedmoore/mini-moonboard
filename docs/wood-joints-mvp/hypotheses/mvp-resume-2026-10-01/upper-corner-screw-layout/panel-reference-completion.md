# N14 panel and screw reference worksheet

The parent completed the finite arithmetic worksheet in
`rawlocal/panel-reference-completion/attempt01`: 396 screw states, 132 complete
panel/receiver screw-group states, 36 panel states and 2,256 gross cut traces
across the six fresh nominal-gap cases. Its status is
`CONDITIONAL_REFERENCE_WORKSHEET_WITH_UNRESOLVED_N14_BASES`, with N14 acceptance
false. The producer preserves the reviewed
104-axis authority, the unadopted 108-axis proposal, all 66 Hillman 42605 screws,
the 47 pending criteria and eight false release flags.

## Frozen force source

All six nominal cases retain 250 lb with the original 2× downward force,
signed 300 N horizontal force, 100 mm hold lever, gravity and the proportional
25 kg accessory allowance. No force, stiffness, geometry or hardware changes
are inputs to this worksheet. Zero-gap sensitivities remain in their original
packets; this API evaluates the requested six nominal-gap states.

| Consumed source | SHA-256 |
| --- | --- |
| `rawlocal/knee-bridge-gravity/attempt01/operator-assessment.json` | `ce69ba58e3c6265d31ab0dfdec1ffac4c019b93fc1106c8f9677ed9b5b2c3f95` |
| `rawlocal/knee-bridge-frame/attempt02/response/comparison.json` | `c3a8ff024fb494032d947aedfd6f00cda8698587b8751b2cec66e4b3af243729` |
| `rawlocal/knee-bridge-frame/attempt02/response/response.npz` | `62bd4116cfb577a0846f4de0d43fbeec6bb704bac7feee530ee673ded1820f90` |
| Current gravity `model.json` | `c14e93e003da72478e2db777cecab1aab7d5a9f7e3b12bdbd6813337f15572c1` |
| Current gravity `model-inputs.json` | `b260af3d53a199e66962caf6c7074086e1d433526e43d263a3f1247ba4c61b99` |
| Current gravity `row-identities.json` | `cdf218780bdabdb8774174c79b37d7c9f554abc6be2e1f817999635e56868b27` |
| Current gravity `operators.npz` | `7877699053a8285b77621ca0cfcb7b09d22b19e5c20729c193e1e5c3f4840e4f` |
| Current gravity `B.npz` | `d109f7db25cb05619e26560e501e7e82f3608fdbb3580f76e64f9beae916128a` |

The fresh gravity mass is 225.19791414318078 kg and its dead factor is
1.1110134616260479. Its global rows still represent 104 bolt axes. The proposal's
four internal ties contribute planning gravity without adding global receiver
rows. This worksheet does not close their shared deformation or transfer a
reviewed-source acceptance to the proposal.

## Entry points and output

[panel-reference-completion.py](panel-reference-completion.py) has inert import,
`prepare(output)` and parent-only `build(output)`. Both require a fresh immediate
child of `rawlocal/panel-reference-completion/`; existing attempts and symlinks
are refused. No source producer, frame/native solve, CAD export, allocation LP,
coupon, software test or review loop is called.

Preparation uses only the standard library. It authenticates literal seed hashes,
the source receipts and their consumed/output closures, joins the current screw
axes to the current receivers and three scalar rows, and reads NPY headers only.
It does not read numerical array values or evaluate a resistance equation.

The completed parent invocation from the repository root is recorded below.
Its `attempt01` evidence is retained; this annotation adds no execution.
`PYTHONDONTWRITEBYTECODE=1` prevents bytecode writes outside the owned paths.

```bash
PYTHONDONTWRITEBYTECODE=1 uv run --no-sync python \
  docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/panel-reference-completion.py \
  --output docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/rawlocal/panel-reference-completion/attempt01
```

Add `--prepare` for standard-library preparation in a different fresh directory.
The equivalent module API is `prepare(Path(...))` or `build(Path(...))` after an
import by file path. Numerical array arithmetic imports NumPy only inside
`build`; it solves no system and adds no dependency.

| Build artifact | Finite calculation |
| --- | --- |
| `screw-states.jsonl` | Exactly 66 screws × six cases: current receiver geometry, all signed scalar forces, simultaneous tension/lateral action, both saved rigid motions at the common physical datum, returned total relative motion, independent head/withdrawal/lateral comparisons, same-state withdrawal/lateral interaction and steel stress requirements. |
| `screw-groups.jsonl` | Every panel/receiver screw group in each case; all three screw-force components and the complete signed six-component wrench about one shared datum, equal-and-opposite receiver wrench, and separately identified saved contact and pair wrenches. |
| `panel-balances.jsonl` | All six panels × six cases: screw, contact and external-load wrenches plus complete body equilibrium residuals. Panel seams remain included in panel balance. |
| `panel-cuts.jsonl` | Finite gross principal-axis cuts before/after saved physical nodal stations: signed section resultants and explicit whole-width mean component comparisons under the preserved panel orientation. |
| `summary.json` | Reference catalogs, exceeded/finite/unsupported counts, simultaneous governing witnesses, source/method limits and retained false acceptance flags. |
| `sources.json`, `producer.py.snapshot`, `receipt.json` | Exact consumed source hashes, executed leaf bytes, output hashes and before/after source authentication. |

Force balance, full moment balance, `q = Da + e − Hf`, screw laws and signed
physical datums are checked against the saved arrays. They authenticate the
arithmetic's use of the existing response; they do not validate product stiffness
or establish a unique loaded pose. Port accounting retains the full `D` moment
and any residual free couple at its recorded point. Opposite complete screw
wrenches are checked at the same datum; a free couple is not discarded or
converted into an invented screw bending field. A numerical refusal leaves a `STOP` receipt
and re-raises its exception. Missing capacities and unsupported geometries are
never zero utilization or passed comparisons.

## Reused methods and assumptions

Only authenticated pure function definitions/constants are loaded through AST.
Module imports and producer entry points from the historical workflows do not
run. The repository has [head-reference-basis.md](head-reference-basis.md) and
[head_check.py](head_check.py); it has no `head-reference-basis.py`. The arithmetic
is therefore reused from the existing attachment helper, with the corrected
head note governing its declared geometry and adjustments.

| Method | Reuse / exact source identity |
| --- | --- |
| [Attachment helper](../panel-attachment/attachment_screen.py) | `head_reference`, `withdrawal_reference`; SHA `c2acb48370cecb3964172e8ab82d3c8999e2836e97025e1bde778bc03cf6b9dc`. Its redistribution/run pipeline is not called. |
| [Generic lateral helper](../panel-attachment/lateral_reference.py) | Six contacting-member yield modes and NDS §12.4 same-state equation; SHA `8bcf31f3e69338de5f16824411ae14567187ce6b92cd05a61f7de3be0de7fbb2`. |
| `fea/dowel_yield.py` | Supplied-input single-shear equations; SHA `d6c318e75c1a720d0b91f810a892e8309ef89735f66f48820ee853b753f8fe45`. |
| `fea/reinforced_panel_checks.py` | APA family `BASE`, stressed-width `size_factor`, existing Group 4 `panel_reference`; SHA `1cf47584c36ab5c513ee74072f66782b0aa3907cca6b0ee940218d84693d634d`. |
| [Material fidelity](panel-material-fidelity.md) | Preserved Group 1, 18.25625 mm panel and strength-axis assumptions; SHA `5c411432f0c0f6abddaefa9ba2c27fe46a2c0b990e2513f3fe65f2f03f2e361f`. |
| [Head reference basis](head-reference-basis.md) | NDS head dimensions/net thickness and single duration adjustment; SHA `577f75fa32889fdb5ee53f1076ebec924132b5251d6e92e571ab0b49e96588d3`. |

The full authentication closure is written into `sources.json`, including the
pinned NDS Chapters 2, 11, 12 and Appendix, physical DOF map, frozen wrench helper,
material/source records and authority. The old attachment response is consumed
only for its twelve withdrawal scenario inputs and equation checks. No old
forces, SPAX resistance, stiffness, installation or hardware dimensions become
Hillman evidence.

Head scenarios preserve the four generic/hypothetical rows in the head note and
three retailer-nominal 9.017 mm rows. Each receives separate `CD=1` and existing
favorable `CD=1.6` comparisons. References are unadjusted when entering the API;
`CD` is applied exactly once. `CM=Ct=1` and the cumulative ten-minute full-peak
duration are explicit favorable assumptions. No additional duration, impact or
dynamic reduction is allowed. **The already adjusted 930.222–984.128 N favorable
head references remain below the documented fresh 1871.246254 N demand.** The
fresh peak has simultaneous lateral action 726.729538 N at upper-left `edge_2`,
A12-rear. The actual worksheet returns that same tuple on
`round_panel_upper_left_edge_2`, `main_upper_left` / `base_rail_top`, with positive
opening 0.695714 mm. It does not combine maxima from different states.

Withdrawal retains timber `G=.45/.50/.55` and effective thread lengths
30, 38.1, 42.333333333333336 and 45.24375 mm. These are sensitivities; `.50` is
the declared DF-L scenario. Parent arithmetic joins every current axis to its
current receiver's gross rectangular frame, insertion interval and grain. A
thread scenario outside that interval, or a non-side-grain insertion, receives
an explicit unsupported result. Occupied CAD diameter/length is not thread
geometry or installed engagement.

Lateral scenarios reuse the existing `.190 in` nominal diameter, `.152 in` root,
80 ksi bending yield hypothesis, 40.41775 mm effective timber bearing length,
18.25625 mm plywood thickness, `Rd=2.2` and plywood `Fe=3350/4650 psi`. Their
unadjusted references are about 386.752/463.413 N. They remain contacting-face
diagnostics; saved positive screw opening is reported separately and cannot be
called confirmation of that condition. Complete Hillman applicability remains
unresolved for every such comparison. The combined equation uses each screw's
simultaneous `T,V` tuple:

```text
R = hypot(T, V)
index = T² / (R W′) + V² / (R Z′)
```

Zero action gives zero arithmetic index. A withdrawal term at least one yields
`NO_FINITE_LATERAL_REFERENCE`, preserving its actual mathematical meaning.
Head pull-through remains independent of this withdrawal/lateral interaction.
Withdrawal-G sensitivities paired with the fixed `.50` timber bearing reference
are labeled reference sensitivities, not newly coherent alternative materials.

Steel records compute root mean tension/shear and the yield stress that would be
required by the same-section von Mises `T,V` diagnostic. **No steel capacity is
assigned.** Bending `Fyb=80 ksi` is not tensile yield/allowable stress. Actual
minimum root/head-neck area, steel tensile/yield basis, profile transition and
screw bending response remain exact missing bases. The scalar frame supplies
no independent screw bending couple. No arbitrary metal strength or zero bend
is used to close the steel comparison.

### Actual screw/head comparisons

The following favorable scenarios all contain 396 finite arithmetic comparisons
and zero gross-geometry refusals. Those counts do not establish Hillman product
conformity or loaded contact. `CD=1.6` is applied once throughout this table.

| Declared comparison | Maximum index | Exceeded states | Same-state governing witness |
| --- | --- | --- | --- |
| Retailer-nominal head, `G=.50`, 17.25625 mm net thickness; 930.222 N reference | 2.011613 | 6 | A12-rear, upper-left `edge_2`; `T=1871.246254 N`, `V=726.729538 N` |
| Same head, favorable gross 18.25625 mm thickness; 984.128 N reference | 1.901426 | 6 | Same `edge_2` tuple |
| DF-L `.50`, hypothetical 45.24375 mm withdrawal thread | 1.090338 | 2 | Same `edge_2` tuple |
| Contacting lateral, plywood `Fe=4650 psi` | 1.677942 | 7 | A12-rear, upper-left `rim_4`; `T=674.388595 N`, `V=1244.127630 N` |
| Same withdrawal/contacting-lateral pair, simultaneous interaction | 1.662421 | 10 | Same `rim_4` tuple |

All 396 steel demand records are finite; **zero Hillman steel resistance records
exist**. At the head-peak tuple, the hypothetical 3.8608 mm root gives mean
tension/shear 159.840362/62.076657 MPa and required same-section von Mises yield
192.638198 MPa. This is a required property under that section hypothesis,
not an assigned capacity or a complete screw bending/head-neck comparison.

## Gross panel cut diagnostics

The saved `F` nodal loads and `−Bᵀf` connector nodal forces permit equilibrium
cuts without a native panel solve. The frozen `B` projection preserves the
original connector footprints; their complete nodal wrenches are checked
against the signed `D` actions. Each principal-axis cut uses the
entire gross section width, both cut halves and the panel midsurface/width-center
datum. It records mean axial force, bending moment and transverse shear per unit
width. The matching Group 1 APA A-A/A-C 23/32-family references come from the
existing helper's declared base values and width factor at `CD=1`. The existing
Group 4 family reference is a separately named sensitivity. Neither changes
the Group 1 elastic response, panel orientation or force allocation.

The reported cut shear is `Q/b = (F_cut · panel_normal)/gross_width`: a
panel-normal transverse resultant associated with out-of-plane bending and
**planar/rolling shear**. It is not in-plane membrane `Nxy`. APA distinguishes
planar/rolling shear from its separate shear-through-thickness category;
the latter addresses forces along panel edges. See [APA's shear terminology](https://dinosaur.apawood.org/frame-for-success)
and [PS 1-22 §§6.2.4–6.2.5](https://www.nist.gov/document/ps-1-22-final-clean-10-02-2023).
These links clarify terminology and units; they supply no replacement strength
values or delivered-product qualification.

The frozen helper's planar reference is **350 lbf/ft of panel width**, converted
to **5.107866028022227 N/mm** at `CD=1` for both named groups. Both demand and
reference are force per width, not MPa or lbf/in. The helper's separate membrane
reference starts at 105 lbf/in with its recorded Group 4 factor `.68`; it is not
the denominator for these transverse cuts. No local through-thickness stress
distribution or veneer/interlaminar stress is returned.

| Gross component | Group 1 maximum ratio / exceeded traces | Group 4 sensitivity maximum ratio / exceeded traces |
| --- | --- | --- |
| Axial | 0.026061 / 0 | 0.042723 / 0 |
| Bending | 0.654407 / 0 | 0.976726 / 0 |
| Planar/rolling-shear resultant | 1.473603 / 24 | 1.473603 / 24 |

The shear witness is A12-forward, `main_upper_left`, cut axis 1, after station
−441.138044 mm from the saved panel datum. Its full gross width is 1217.6125 mm
and signed `Q/b` is −7.526965546630302 N/mm. The saved comparison is
`abs(Q/b) / 5.107866028022227 = 1.4736027737095434`. The 24 counts are cut traces,
including before/after records, not 24 independently failed panels. This
exceeds the declared gross reference under the preserved assumptions; it
does not establish local rolling-shear failure, actual plywood failure or a
qualification of the local hold/panel connection. The below-reference axial
and bending means likewise leave local strength unresolved.

### Unsupported local panel conditions and remaining bases

These are gross mean component diagnostics. A below-reference mean does not
qualify local plate stresses, effective width, hole/countersink ligaments,
kicker cutouts, local head transfer, biaxial interaction, panel buckling or
serviceability. The existing helper quotes APA D510C PDF SHA
`6141e0fe02ad0db8ddec20becf2ec25c85accd21c9796e51411d19448e5762ca`;
this worksheet authenticates the helper's recorded method, not new PDF bytes.
Purchased Roseburg AC identity is retained; delivered grade/group, strength-axis
placement and layup/profile applicability remain declared assumptions.
Every cut retains `local_plate_or_net_section_strength_ratio=null` and
`complete_panel_acceptance=false`. Local hold/head bearing and load spreading,
net-hole/countersink sections, laminate/rolling-shear stress distribution,
biaxial strength, buckling and kicker-cutout applicability have no completed
local strength comparison here. These panel limits are separate from the
finite screw/head comparisons above.

The separately returned panel/receiver motions are their actual saved rigid
motions at each common screw datum. Total signed relative motion includes the
saved elastic contribution. Individual absolute elastic motions are not stored
in this response, so the API identifies that missing field explicitly. It does
not manufacture two elastic poses from their relative difference.

The remaining N14 limits are product/profile and steel conformity, actual thread
reach and pilot/countersink compatibility, supported loaded-contact/screw
stiffness, local/net panel strength and complete receiver/backer continuation.
Saved group/contact balance is usable arithmetic evidence within the source
model; it supplies no new compatible redistribution. N09 washer work, other
receiver/member resistances, stability and common-knee deformation retain their
own ownership and leaves. Reference exceedances may guide model decisions;
they are not observed physical failures or new authority/release decisions.

## Actual evidence and retained work

The parent independently matched all 108 source pins and eight output hashes
for `attempt01`. The receipt records source authentication before and after
the completed arithmetic. Exact leaf identities below are relative to
`rawlocal/panel-reference-completion/attempt01/`.

| Actual leaf | SHA-256 |
| --- | --- |
| `producer.py.snapshot` and frozen API source | `1943198db40ed6729f6c93c3a1196e1642d3a3843fb2bbf5e826aa6b35a116b1` |
| `summary.json` | `dfa8a93d686e82b5ee8099ad55fce66f436d1720ab5fb51b4cdf6c1b2761c6f5` |
| `receipt.json` | `5b42272f49c1924546abab3bd4d036a0a95f7afb2700055fb2e769ab56a3db91` |
| `screw-states.jsonl` | `d609d0ad8dac84400bea9eff9c7f17c9f072e2c7f9bf5e002f2a72d94fb32841` |
| `screw-groups.jsonl` | `0282923a6fffc513603b2aa40c9908a9a37e70816db23431412122d91744de5e` |
| `panel-balances.jsonl` | `55fe35a743334c119b123b3ff2cd7638c98a53800303e6fa524944a302e7cfbd` |
| `panel-cuts.jsonl` | `8078ad3ff8237af2ee51d3ce01f3036613a77eadb26864ed00ac3ade2314b398` |
| `sources.json` | `bb4ef5b08a4cfa58218a9f8da2749d4b5bc447d3062abbb3c68ff718b2a2792f` |
| `.gitignore` | `cdbcae15105d6b781e620813c79c7e868740d4e9cc53ce6f5fcbbc12387adf4b` |

Before the parent build, the worker ran AST parsing, Ruff and standard-library
`prepare(output)` only. This annotation reads the completed JSON evidence and
updates this Markdown only; it runs no preparation, build, software test,
frame/native/CAD solve, coupon or review loop. The ignored attempts remain local
evidence. The worker leaves staging and publication to the parent.

| Preparation leaf | SHA-256 |
| --- | --- |
| `rawlocal/panel-reference-completion/prepare04/producer.py.snapshot` | `1943198db40ed6729f6c93c3a1196e1642d3a3843fb2bbf5e826aa6b35a116b1` |
| `rawlocal/panel-reference-completion/prepare04/summary.json` | `535dd13a3724125ba200e08ee2bec36eecc1f05aec5c58ba27839833d68a3c2a` |
| `rawlocal/panel-reference-completion/prepare04/receipt.json` | `1be1c9d9bf8c11729441e4cd72e4089d8a3672ed524f6d6b1cd51bb48dc0b3b4` |
| `rawlocal/panel-reference-completion/source-investigation.txt` | `71c2e7d737789e5a8f07245c1c853fd0b552d6822f1237c922e5f8eb42213d5f` |

The historical `prepare04` status is `PREPARED_NO_MECHANICS_EVALUATED`;
`attempt01` now supplies the actual conditional comparisons above. Active next
action is parent publication and integration into the existing owned
qualification/disposition entries. The API source and this annotated Markdown
are frozen for that publication. Existing raw runs remain dependencies;
`prepare01` through `prepare03` retain earlier snapshots. Nothing is pruned or
selected for archive. The bounded source investigation used `gpt-6.1-sol` with
configured `xhigh` effort and supplied method/input facts only.
