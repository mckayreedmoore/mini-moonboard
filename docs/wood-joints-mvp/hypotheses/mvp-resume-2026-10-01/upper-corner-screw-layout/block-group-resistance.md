# Current upper-block timber group and splitting worksheet

The completed compatible responses preserve the complete force **and moment**
transfer at all **48 existing exterior host cuts**, covering both actual cleats,
both hosts and six current cases. This finite equilibrium check makes those
exterior demands reusable after individual bolt redistribution. It establishes
no numerical resistance for the complete oblique timber group. The applicable
NDS provisions below explain the remaining local timber requirement without
reopening completed component checks.

## Inputs and bounded method

[The producer](block-group-resistance.py) reads the completed
[right block](upper-right-block.md), its two compatible host pairs and the
completed actual [left block](upper-left-block.md). It imports no mechanics or
CAD producer. The left response supplies its own forces, geometry, host datums
and mapped W; right results supply no left acceptance. Left component replay
remains with the parent's `upper-left-block-components.py`.

Each block has four bolts and 32 face cells. The current cleat section is
**88.9 × 139.7 mm**, with **119.7 mm** along grain. The rail bolts occupy one
grain row at **33 mm** pitch; the side bolts occupy two separate grain rows at
**67.85 mm** transverse spacing. The 139.7/38.1 mm cleat/rail grips and
88.9/88.9 mm cleat/side grips remain the completed hypotheses. Current sections
and STEP bindings come from the frozen correction proposal. The operator
metadata supply grain axes; their older cleat depth and original STEP are
excluded from current section claims. Existing finished tangent paths and
supported annuli are reused as geometry, without another resistance replay.

For each host and case, the producer adds both saved bolt wrenches and the
saved face wrench, then shifts all six components to the block's common datum:

```text
M_new = M_old + (old_datum − new_datum) × F
reaction_on_rigid_cleat = −wrench_on_host
```

The opposite host reactions are the existing rigid model's energy-dual
reactions. Their whole-block sum closes with the original mapped W included
once, including its assigned hardware and couple. The producer neither adds
gravity to host drives nor assigns the block W to an invented point for
internal cleat cuts.

For the host cuts, it encloses the **full** current face, bore grips/radii and
modeled washer annuli in the actual host grain direction. Every saved cut
contains the whole target interface in one half and none in the other. Hence,
with remote host actions and body loads frozen:

```text
ΔQ_interface_at_cut = Q_compatible_at_cut − Q_source_at_cut
Q_internal,new = Q_internal,saved − ΔQ_interface_at_cut
```

The subtraction applies only to the half containing the interface; the other
half retains its saved complete-host wrench. A cut intersecting that interface
would return an unassigned result. The 1e-6 mm classification tolerance covers
pinned coordinate rounding at a touching terminal face; it moves no cut.
Other contacts whose footprints cross these cuts remain recorded, with their
frozen source allocation. This is exterior point-action equilibrium within the
existing model, rather than recovered timber traction or a stress field.

## Finite results

The lightweight run completed 12 block states, 24 host states and 48 complete
host cuts. All 48 cuts satisfy the exterior-interface condition. Maximum
source-to-compatible interface differences are **0.000018156 N** and
**0.000827864 N·mm** at the common datum, within the completed block tolerances.
Both transferred couples and sampled bolt-seat moments remain in the output.
The greatest interface moment component is **35,626.420 N·mm**; whole-block
moment cancellation does not remove it from local wood transfer.

These maxima are selected from individual simultaneous records. The producer
forms no combination of independent peaks and assigns no capacity.

| Block / host | Largest absolute exterior host transverse cut force, N | Case |
| --- | ---: | --- |
| Actual right / top rail | 1,040.454938 | K12 rear |
| Actual right / right side | 1,586.202557 | K12 rear |
| Actual left / top rail | 922.106469 | A12 left |
| Actual left / left side | 1,608.477333 | A12 rear |

The table uses the host's recorded section-v direction. It is a complete-host
cut force, **not** a local point load or splitting utilization. In particular,
the left side's governing complete-host case differs from its governing
individual bolt case.

For example, right K12-rear rail transfer on the cleat, in cleat grain/u/v
coordinates at its common datum, is approximately:

```text
F = [1043.383299, 58.447985, −331.249359] N
M = [12092.893894, −35587.907615, 175.833568] N·mm
```

Its two same-state parallel bore components are 531.464643 and 511.918656 N.
The side interface simultaneously supplies −1050.152393 N along cleat grain,
323.182267 N in cleat v, and its own full couple. The opposed grain components
are transferred through the same block; their sum is no net-section or
tear-out acceptance. Every interface in this packet has a transverse force
above its numerical residual tolerance, including the lightly loaded cases.

## Applicable NDS provisions

The cached **2024 specification** PDFs were read directly. Filenames containing
`withCommentary` do not establish commentary content. The worksheet relies on
the specification and nonmandatory Appendix E, with no unverified commentary
interpolation.

| Primary provision | Application to this block |
| --- | --- |
| [§§3.1.2–3.1.3, p.16; §3.8.1, p.24](https://web-media.awc.org/wp-content/uploads/2021/12/17210019/AWC_NDS2024_withCommentary_20240718_AWCWebsite_Chapter-3-Design-Provisions-and-Equations.pdf) | Use the net section after removals and account for eccentric loading and member sharing. Summed area alone supplies no regional force or bending distribution. The staggered parallel-array rule in §3.1.2.2 also requires attention: side stations lie 16.5 mm from adjacent rail stations, below both 4D comparators (25.4 and 31.75 mm). These orthogonal bore families do not establish that rule's complete net-section interpretation by themselves. |
| [§11.1.2, p.70](https://awc.org/wp-content/uploads/2026/09/AWC_NDS2024_withCommentary_20260911_Website_Chapter-11-Mechanical-Connections.pdf) and [§12.6.3, p.100](https://awc.org/wp-content/uploads/2026/09/AWC_NDS2024_withCommentary_20260911_Website_Chapter-12-Dowel-Type-Fasteners.pdf) | Evaluate member capacity and local multiple-fastener stresses by engineering mechanics. The exterior cut replay supplies applicable demands, while interior ligament stresses remain unestablished. |
| [Appendix E.1–E.4, pp.174–175](https://awc.org/wp-content/uploads/2026/09/AWC_NDS2024_withCommentary_20260911_Website-Appendix.pdf) | This optional procedure concerns parallel-grain fastener loading. E.2 uses `Ft′ A_net`; E.3 uses critical shear paths and a triangular shear distribution; E.4 uses half each bounding-row resistance plus `Ft′ A_group-net`, with alternate critical groups for unequal row spacing. The actual orthogonal array, oblique actions and retained moments require additional transfer and interaction evidence. A parallel force projection or summed individual path references cannot supply complete-group resistance. |
| [§11.3.6.1–.3, p.74](https://awc.org/wp-content/uploads/2026/09/AWC_NDS2024_withCommentary_20260911_Website_Chapter-11-Mechanical-Connections.pdf) | Cg concerns equal-diameter rows aligned with load and their applicable member areas. It is distinct from wood net-section, tear-out and splitting. The existing conditional rail multiplier stays in its completed component scope; no new four-bolt Cg or second redistribution penalty is imposed. |
| [§12.5.1.2–.3, pp.97–99; §12.6.2, p.100](https://awc.org/wp-content/uploads/2026/09/AWC_NDS2024_withCommentary_20260911_Website_Chapter-12-Dowel-Type-Fasteners.pdf) | Applicable geometry factors and detailing remain separate from stress acceptance. Actual moment retention matters for angled groups; the compatible side response does not establish uniform sharing merely because two bolts exist. |
| [§3.8.2, p.24](https://web-media.awc.org/wp-content/uploads/2021/12/17210019/AWC_NDS2024_withCommentary_20240718_AWCWebsite_Chapter-3-Design-Provisions-and-Equations.pdf), [§11.1.3, p.70](https://awc.org/wp-content/uploads/2026/09/AWC_NDS2024_withCommentary_20260911_Website_Chapter-11-Mechanical-Connections.pdf), and [Table 12.5.1C note 2, p.99](https://awc.org/wp-content/uploads/2026/09/AWC_NDS2024_withCommentary_20260911_Website_Chapter-12-Dowel-Type-Fasteners.pdf) | Address actual induced perpendicular tension and the note's medium/heavy tension-side beam suspension geometry. These clauses provide no numerical sawn-lumber Ft⊥. A transverse resultant or couple alone demonstrates neither that suspension geometry nor tensile stress. A justified local transfer/reinforcement procedure is needed where the actual stress mechanism requires it. |

For the shaft's **own axial channel**, both outer washer seats receive inward
compression through the existing through bolt. This establishes a mechanical
normal-transfer topology within the completed hypothesis. It supplies no
automatic reinforcement qualification for bore-induced cracking, between-group
ligaments or every moment-induced stress. The saved EN 1995 characteristic
F90 values remain historical reference fields; no design conversion or ratio
is adopted here.

## Completed evidence and exact remaining requirement

The right component calculation already supplies its unchanged conditional
single-shear, individual finished-path, supported-annulus and smooth-bolt beam
references. Its recorded maxima remain 0.813949, 0.160367, 0.770232 and
0.313740, respectively, within their existing scopes. Bolt fit, annulus
support and hardware length are completed evidence. Left compatible mechanics
are also complete; the parent owns its corresponding component replay.
Neither task is duplicated here.

The remaining timber input is an applicable **local transfer and resistance
evaluation for the current finished cleat**, including critical net sections
and interacting ligaments under both simultaneous host boundaries, bore
distributions, normal contacts, seat moments and original W. Its method must
retain sectional bending/shear and regional sharing, and identify any actual
perpendicular-tension mechanism and adequate existing transfer route. The
current rigid block has no elastic timber stress field or demonstrated sharing
between disconnected cut regions. Grade/reference adjustments and any R/T
constitutive applicability must stay within their recorded basis. No clear-wood
Ft⊥, fraction of Fv, invented interaction law or characteristic conversion
fills that input.

The producer's `host_states` retain the exact same-state interface wrenches,
bolt/end-moment witnesses, finished grain-row paths and exterior complete-host
cut resultants for the parent's ongoing local mechanics. The original contact
and bore distributions remain in the pinned pair/left results. Existing
exterior demands are usable now; internal cut stresses and group/splitting
resistance remain distinct. This worksheet changes no model, hardware,
geometry, formal criterion or qualification flag and adds no general approval
requirement.

## Replay and source receipt

Use a fresh output directory within the owned ignored folder:

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 \
uv run --no-sync python \
  docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/block-group-resistance.py \
  --nds-chapter3 /tmp/nds2024-ch3.pdf \
  --output docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/rawlocal/block-group-resistance/attempt03
```

Chapter 3 is the existing shared cache, authenticated independently. An
equivalent cache path may be supplied with the same required hash. No PDF
parser is needed to replay the worksheet. Source pins are checked before
arithmetic and again before the receipt. Raw outputs are ignored; only this
worksheet and producer are new maintained files.

| Binding | SHA-256 |
| --- | --- |
| Producer | `e5df5f81168a0e700948816a5c292c521593b328ab86fb72b1a2e2f0cd98b3b0` |
| [Current result, attempt02](rawlocal/block-group-resistance/attempt02/checks.json) | `0a69cd84902c9105f5e6b8f3c70e59efaae9ac56bc4c3238935d97a4185d210b` |
| Right block | `0b0b392b9e5e411173395671878c09e0be303abd4885f48d1e7e7b61d8f6a89b` |
| Actual left block | `5e8c52e529f58f9276c4c67f554fa0b74a990dd501e347e59434aa244e628ed0` |
| Right rail / side pairs | `e0cccb56abb94ed16c322da888cd64a9904c4e49d1e34f573a6903c8b8b98d3d` / `b507a5a501737c89814a471eee6a12749a3c54224f5444b2c5d583020e875ba7` |
| Existing component geometry/result | `401b8876dc3a96b553c847f1029a5a9200ba3f45af5493f64edd61fdc6bc42b6` |
| Current model | `b5f9b87b70c4a9920372a3443a55e37dfe34351fb9ac8210b299c1360fb93626` |
| Frame comparison / response | `bea6cbc330af3cdb20499d774a8f6bb24481d687c3150adb01ede18e4c1d50ca` / `0625196497b0dbc7b297724d7b9947f7c7c61bb282cd4d9681705629302c76c7` |
| Cached NDS 2024 Chapter 3 | `205df74e16f632dfe78211e99bfa5dfa8b9f8dd316e9c5fa1316493f795ec644` |
| Cached NDS 2024 Chapter 11 | `45a3d78de1a4fba573589be0fc776e37bd581e4cedec24e38d63856161092d33` |
| Cached NDS 2024 Chapter 12 | `53f6ec05dfd1ceabeccd4d6e88c342111678d3da4631ee7b482b706f77c1780f` |
| Cached NDS 2024 Appendix | `1fa2bcf52803b1bbed8ea30cf13551dd5f76c90bf110ac475b401f81d116ec31` |

Targeted Ruff passed. Only lightweight arithmetic and source authentication
were run. No software tests, review loop, native/CAD/frame solve, staging or
commit were performed. The receipt retains the producer snapshot and all 30
source bindings, including each current corrected cleat STEP hash.
