# WJ-03 / WJ-04 wood limit-state basis

Status: **method and input specification only; no wood resistance, pass, or
failure result.** This note binds to the current WJ-03 outer-node inventory
and WJ-04 `narrow_x95p25_ordinary_bolt_candidate` trial. Geometry is
development-only; material, delivered cuts, selected hardware, and fresh
WJ-09 actions are unverified. A missing applicable method or input remains
unresolved, never zero demand or zero utilization. Bolt steel, dowel-yield,
and washer-bearing methods are tracked separately in
[`bolt-resistance-basis.md`](bolt-resistance-basis.md).

## Candidate geometry and grain map

Use the current source-bound global grain vectors and transforms in
[`source-inventory.json`](source-inventory.json),
[`interfaces.json`](interfaces.json),
[`wj04-probe.json`](wj04-probe.json), and
[`wood_joint_wj04_config.py`](../../mini_moonboard/wood_joint_wj04_config.py).
The historical X/T/N labels in an old report are coordinates, not a substitute
for transforming each current global vector.

| Joint / member | Modeled section | Global grain | Bolt axis and row direction |
| --- | --- | --- | --- |
| WJ-04 rail host | 38.1 × 139.7 mm; grain along source X | `+X` | Two provisional axes `+T`, X pitch 25.4 mm |
| WJ-04 principal host | 38.1 × 139.7 mm; grain along source T | `+T` | Two provisional axes `−X`, N pitch 27 mm |
| WJ-04 cleat | 95.25 × 38.1 × 119.7 mm (X × T × N); no primary notch | `+N` | Receives both orthogonal groups: rail `+T`/row X and principal `−X`/row N |
| WJ-03 outer spine | 88.9 × 88.9 × 269.95 mm, two mirrored | `+Z` | Spine/post and spine/side groups use `±X` bolt axes |
| WJ-03 rear bridge | 383.2 × 88.9 × 88.9 mm, two mirrored | `+X` | Bridge/spine and bridge/link groups use `+Y` bolt axes, row along X |
| WJ-03 under-header link | 185.2 × 88.9 × 88.9 mm, two mirrored | `+X` | Bridge/link uses `+Y`; link/header uses `−Z`, row along X |

WJ-03 host grains are source post `±Z`, side member `±T`, and header `±X`;
each mirrored sign comes from its part transform. Each of its five bolted
groups per side has two provisional 6.35 mm bolt axes and 7.5 mm modeled
bores. The spine/post pair is 42.05 mm apart along Z; spine/side centers are
staggered by global XYZ `(0, 28, 52) mm`; bridge/spine, bridge/link, and link/header
rows are 35, 72.35, and 35 mm along X. These vectors describe row geometry,
not a loaded direction. The unbolted spine/header end contact remains a
separate bearing/contact check.

WJ-04 cleat source-projection bounds are X = 89.05–184.30, T =
1353.874–1391.974, N = 229.841–349.541 mm. Rail-group centerlines are at
X = 127.15 and 152.55 mm, N = 265 mm, along `+T`; principal-group centerlines
are at T = 1372.924 mm, N = 293 and 320 mm, along `−X`. Its four orthogonal
bores are presently nominal CAD geometry, not a delivered bore specification.
The face groups are on separate cleat faces and their section effects must be
combined in the cleat check. Unsigned geometry distances are 38.1 mm from the
rail's first bolt to its grain-X end; 35.159 and 84.541 mm from the cleat's
rail-group row to its grain-N ends; and 19.05 mm to each cleat T edge at the
principal row. These are inputs for later signed checks, not loaded-edge
classifications or capacity conclusions.

## Signed directional classification

At each interface and for each wood member separately, transform the
member's unit grain vector `g` and bolt unit axis `a` into the same global
frame as the signed member-on-connector wrench. Verify the current side-grain
condition `a · g = 0` for each layer; if a changed axis is not perpendicular to
grain, the lateral/grain decomposition and Appendix E applicability need a
method that covers that geometry. For each resolved bolt force `F`, calculate:

```text
F_axial   = (F · a) a
F_lateral = F − F_axial
F_parallel = (F_lateral · g) g
F_cross    = F_lateral − F_parallel
```

Retain the signs and both transverse components. `F_axial` is carried to
separate bolt-tie/washer/wood-bearing checks; it is not lateral dowel load.
`F_parallel` sets
the signed grain direction for loaded-end and parallel-row checks.
`F_cross` identifies cross-grain demand and its loaded edge; it does not
become parallel-grain row tear-out by relabeling the axes. Repeat for the
equal-and-opposite action on the other member using that member's own grain
vector. Do not infer a shared grain direction for a two-member joint.

For each signed load component, measure the bolt center to every finite
finished boundary along both `+g` and `−g`, and along both cross-grain sides
in the member plane perpendicular to the bolt axis. Identify the loaded end
or edge only from the signed component and member's actual cut frame. Include
nearby holes, notches, reliefs, and free edges as boundaries. For an oblique
resultant, preserve and check the grain-parallel and cross-grain components
with methods applicable to each; do not select the controlling edge from the
unsigned resultant alone.

Separately apply NDS §§12.1.2–12.1.3 and 12.5.1 (Tables 12.5.1A–D) to actual
selected bolt diameter, direction, pitch, and end/edge distances. These are
connection geometry/detailing limits; a nominal 4D/7D comparison alone is not
the applicable table check or a wood strength check.

The WJ-04 row lies along the host rail's grain X but across the cleat's grain
N; its principal-bolt row lies along the cleat's grain N but across the
principal host's grain T. The WJ-03 groups likewise differ by member: the
bridge/spine row is parallel to bridge grain and cross-grain to spine; the
spine/side row is oblique to both; the other row alignments are listed above.
Thus each host and connector needs a separate signed classification.

The current WJ-04 early mechanics record carries six old selected-angle
group wrenches, not current wood-joint cases or per-bolt actions. Four of 211
bound source files differ from the historical snapshot in each case. Its
idealized contact/bolt statics witness has no stiffness, contact-pressure
distribution, wood resistance, or load-sharing basis. It may guide input
reconciliation only; it cannot populate signed current end/edge classifications
or constituent capacities ([diagnostic](wj04-early-mechanics.md)).

## Wood failure-mode computation contract

For each WJ-03 and WJ-04 host and connector member, and each fresh WJ-09 case:

1. Bind the exact finished part, source transform, grain vector, cross-section,
   complete bore list, and every other cut. Use actual delivered bore sizes
   and member bounds when known. The 7.5 mm modeled bores and nominal bolt
   axes in current JSON files are geometric placeholders; they are not drill,
   stock, or resistance inputs.
2. Retain the signed six-component wrench at a declared interface and member
   datum. Shift it to each bolt-group datum without dropping moments. Emit
   per-bolt actions only from a sourced stiffness/contact distribution model;
   a rigid equilibrium witness or equal division of group force does not
   establish load sharing. If only group action is available, per-fastener
   wood checks remain `UNRESOLVED_DEMAND`.
3. Check every candidate net section normal to a force path. Use the actual
   net area after the union of all intersecting bores and cuts, not gross
   section or bores subtracted twice. NDS §3.1.2 defines the net-section
   basis; §§3.8.1–3.8.2 cover tension parallel/perpendicular to grain.
   Where Appendix E applies, evaluate its net-tension component:

   ```text
   Z′_NT = F′_t A_net                 (NDS-2024 Appendix E.2)
   ```

   `F′_t` must include applicable design-value adjustments. Check the actual
   tension direction and net plane. Do not use a parallel-to-grain tensile
   value for tension perpendicular to grain.
4. For a fastener row loaded parallel to grain, and only after proving the
   Appendix E geometry and loading assumptions fit, calculate every applicable
   row tear-out path:

   ```text
   Z′_RT,i = n_i F′_v A_critical,i / 2       (NDS-2024 Appendix E.3)
   ```

   `A_critical,i` is the critical area defined by Appendix E for the actual
   member and shear-line count. For the standard one-row path with two shear
   planes flanking the row it reduces to `2 t s_critical`, so
   `Z′_RT,i = n_i F′_v t s_critical`, with
   `s_critical = min(loaded-end distance, row pitch)` where that row geometry
   applies. Do not reuse this simplification for another group layout.
5. For a connected parallel-grain group satisfying Appendix E, calculate each
   permitted group failure area, including the nonuniform-row cases required
   by E.4.1, and check:

   ```text
   Z′_GT = (Z′_RT,1 + Z′_RT,n) / 2 + F′_t A_group-net
                                            (NDS-2024 Appendix E.4)
   ```

   `A_group-net` is the actual critical net area bounded by the group rows.
   Appendix E row/group equations are not cross-grain splitting equations and
   do not themselves provide fastener load distribution or a complete joint
   resistance.
6. Retain cross-grain splitting as a separate limit state. NDS §§3.8.2 and
   11.1.3 require attention to tension perpendicular to grain and connection
   eccentricity but do not give a general formula for every new bolt-group
   topology. The candidate's `supplemental_EC5_splitting` obligation stays
   pending until its exact Eurocode edition, clause, inputs, factors, and
   applicability to each WJ-03/WJ-04 member and load path are shown, or a
   supported replacement is mapped. The existing legacy EC5 screen is an
   analogy, not candidate evidence. Do not accept/reject a joint from a
   conditional 4D/7D comparison alone.

For every implemented mode, report the actual case/interface/member, selected
method and version, load/grain angle and sign, edge/end distances, critical
section or group area, material values and adjustment factors, demand,
resistance, ratio/margin, and source identity. Use `PASS` or `FAIL` only when
geometry, material, demand, and method are all valid; otherwise report the
specific unresolved state: `UNRESOLVED_GEOMETRY`, `UNRESOLVED_MATERIAL`,
`UNRESOLVED_DEMAND`, or `UNRESOLVED_METHOD`.

## WJ-04 cleat internal section check

The cleat is a short 95.25 × 38.1 × 119.7 mm solid member with grain along N.
It receives two separate host interface wrenches through orthogonal faces,
two 2-bolt groups, and compression-only face contact. Its section actions
therefore need a resolved transfer model for both groups and both contact
patches. Translate every simultaneous interface wrench to a shared cleat
datum; establish the reactions and load sharing; then recover the six
section resultants on cuts normal to grain: axial force `N_N`, shears `V_X`
and `V_T`, bending moments `M_X` and `M_T`, and torsion `M_N`. Also check
sections with other orientations where they expose a weaker net path. The
historical statics witness cannot supply this model.

At each critical section, use the union of all four actual cross-bores plus
any finished cuts to obtain the net area, centroid, principal section
properties, and shear/torsion properties. For regular sections where NDS
member provisions apply, compute axial and bending stresses from the actual
net section and use the applicable Chapter 3 checks; NDS §3.9.1 gives the
uniaxial tension-plus-bending conditions:

```text
f_t / F′_t + f_b / F*_b ≤ 1.0       (Eq. 3.9-1)
(f_b − f_t) / F**_b ≤ 1.0           (Eq. 3.9-2)
```

Use other applicable Chapter 3 provisions for compression, shear, and
stability. A multiply bored, biaxially bent, torsion-loaded cleat is not
automatically covered by the uniaxial equations above. Do not use the gross
rectangular section or a two-face equilibrium witness as a bending/torsion
capacity. Where the finished-section shape, biaxial interaction, torsion,
local stress concentration, or contact transfer lacks an applicable NDS
method, record `UNRESOLVED_METHOD` until a supported rational analysis or
test method is provided.

## DF-L No. 2 and size applicability

The candidate basis assumes Douglas Fir-Larch No. 2 under the recorded dry
service assumptions. The delivered species group, grade, moisture/treatment,
dimensions, and connection-zone condition have not been observed; these are
material source/receiving inputs, not an outside-review gate.

- WJ-03 connector blanks are 88.9 × 88.9 mm nominal-4×4 dimension lumber,
  crosscut only. Use the correct 2024 Supplement Table 4A dimension-lumber
  row/size category and applicable NDS §4.3 factors. NDS §4.1.7.2 exempts a
  crosscut-only length change from §4.1.7.1 regrading, subject to the stated
  grade/condition and final-section checks.
- WJ-04 cleat final geometry is 95.25 × 38.1 mm in cross-section. The current
  stock route rips a 2×6 along its length to make the 95.25 mm dimension.
  NDS §4.1.7.1 requires resawn/remanufactured structural lumber to be
  regraded. The original 2×6 stamp alone cannot establish DF-L No. 2 values
  for the ripped cleat. Use final-section grade evidence or a suitably
  graded source; this is a specific material validity check, not a blanket
  external grading prerequisite. Once established, use its applicable Table
  4A dimension-lumber size class, not Table 4D post/timber values.
- Verify a recognized grade mark or inspection certificate, actual species
  group, actual section and moisture/treatment condition before assigning
  reference design values (NDS §4.1.2). Apply the relevant NDS Chapter 4
  adjustments; do not use a base tabular value as an adjusted connection
  resistance. The existing reference helpers encode dry DF-L No. 2 Appendix E
  inputs `F_t = 575 psi` and `F_v = 180 psi`; these are base inputs only, not
  final adjusted values or accepted WJ-03/WJ-04 capacities.

## Inputs still required

- Current, fingerprint-matched WJ-06 finished parts, cuts, bores, all-member
  coordinate frames, actual grain vectors, and finite boundaries.
- WJ-09 fresh six-case complete-frame actions, shifted signed wrenches,
  group-level load sharing/contact distribution, and a justified per-bolt
  allocation where a bolt check needs it.
- Finished stock dimensions and valid grade/species-group/material basis,
  including post-rip WJ-04 cleat grade evidence; material adjustment factors.
- Selected bolt diameter and actual bore size; exact group row directions,
  actual shears/planes, and all existing/member cuts in critical sections.
- Applicable cross-grain splitting method for each topology and supported
  section method for WJ-04 cleat bending/shear/torsion with orthogonal bores.

Until these inputs and methods are bound, all wood resistance rows remain
pending. This note is a computation specification, not a fabrication,
structural, or climbing release.

## Primary references

- [AWC 2024 National Design Specification](https://awc.org/resources/2024-nds/):
  §§3.1.2, 3.4, 3.8, 3.9, 4.1–4.3, 11.1, 12.1, 12.5, Appendix E.
- [AWC 2024 NDS Supplement](https://awc.org/resources/2024-nds-supplement/),
  Table 4A; use the Supplement and NDS as one matching edition.
- [AWC 2024 NDS Chapter 3 PDF](https://web-media.awc.org/wp-content/uploads/2021/12/17210019/AWC_NDS2024_withCommentary_20240718_AWCWebsite_Chapter-3-Design-Provisions-and-Equations.pdf).
- [AWC 2024 NDS Chapter 4 Supplement PDF](https://awc.org/wp-content/uploads/2026/08/AWC_NDS2024-Supplement_20240719_Chapter-4-Reference-Design-Values_Website-1.pdf).
- [AWC 2024 NDS Chapter 12 PDF](https://awc.org/wp-content/uploads/2026/08/AWC_NDS2024_withCommentary_20250328_WebsiteChapter-12-%E2%80%93-Dowel-type-fasteners.pdf).
- [AWC 2024 NDS Appendix PDF](https://web-media.awc.org/wp-content/uploads/2021/12/17210019/AWC_NDS2024_withCommentary_20240719_AWCWebsite_Appendix.pdf).
- [AWC 2024 NDS errata/addenda, March 2026](https://awc.org/wp-content/uploads/2026/03/2024-NDS-Errata-and-Addenda-03.23.26.pdf).
- [BSI listing for BS EN 1995-1-1:2004+A2:2014](https://knowledge.bsigroup.com/products/eurocode-5-design-of-timber-structures-general-common-rules-and-rules-for-buildings):
  primary-standard reference for a supplemental EC5 splitting method; exact
  clause and applicability remain to be resolved before use.

Repository calculation aids are limited to their documented reference scope:
[`bolted_timber_checks.py`](../../mini_moonboard/bolted_timber_checks.py)
contains conditional net-tension and parallel row/group tear-out arithmetic;
it does not perform splitting, load allocation, cut integration, or complete
joint acceptance.
