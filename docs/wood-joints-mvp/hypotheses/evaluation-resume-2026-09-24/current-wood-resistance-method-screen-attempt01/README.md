# Current wood member resistance method screen — attempt01

**Date:** 2026-09-27. **Status:** method applicability only; no capacity or
criterion is resolved.

This note screens wood-member resistance methods for
`compact-floor-flush-wood-joints-development`, revision
`led-clearance-2x6-runner-seated-blocks-v1`, reviewed at `b1e8707d`. It does not
change the reviewed geometry or adopt a design-value scenario. The selected
baseline remains `compact-floor-flush-development`.

MVP-E may use explicitly source-bound analytical scenarios for material,
grade, and grain frames before physical receiving. Such assumptions support
conditional analysis only; they do not establish what was delivered or
physically regraded. WJ-11 receiving and actual-disposition fields may remain
blank as stated conditions. Any unspecified analytical input remains a gate
or must be handled as a named scenario range.

## Current evidence state

The current representative ordinary joint has three timber members, four bolt
stacks, and three wood contacts. The plan records no accepted response or fresh
current-candidate member/joint demands. The recent transient diagnostic did not
produce an accepted equilibrium response. No historical or analyst-selected
unit actions are substituted for current signed demands. Member demand/capacity
ratios therefore cannot be calculated; the criteria listed below remain
`pending`.

The two material-frame maps cover 20 source-frame timber members and 24
connector blocks. They map conditional analytical longitudinal axes, not
observed grain in delivered pieces. The frame map leaves each board's
transverse ring orientation unresolved. The block map retains two conditional
transverse-axis cases per block. Neither map assigns grade or resistance
values. Six plywood panels are outside these timber maps and this screen.

## Member criteria and applicable methods

The named methods are candidate-specific routes into the published U.S. wood
design basis. For an analytical scenario, bind the assumed member, material
identity, grain frame, finished section, load path, and current demand. Actual
receiving evidence is separate and is not implied by the scenario.

### Bending and combined axial force

**Criteria:** `sampled_net_member`,
`taper_actual_net_section_normal_resistance`,
`header_gross_full_length_stability`, and `sampled_member_stability`.

For member flexure, use the 2024 NDS bending provisions with the matching 2024
NDS Supplement reference bending value `Fb`, scenario section properties, and
all applicable adjustments. When axial force and bending act together, use the
NDS combined axial/bending provision for the signed load state. Compression
cases also need the applicable column and member stability treatment. The method
must use each member's local longitudinal and transverse frame, not global
coordinate labels.

**Gates:** scenario-bound final cut/bore section and section axes; specified
unsupported lengths and restraint conditions; source-bound product, species
group, grade, and conditional grain frame; applicable service/design
adjustments; and fresh simultaneous axial and moment demands. `E` or `Emin`
may support the applicable stiffness or stability calculation only after a
valid product/table match. An elastic material map is not a resistance value
or a joint-stiffness disposition.

### Tension parallel to grain and net section

**Criteria:** `sampled_net_member` and
`taper_actual_net_section_normal_resistance`.

Use the NDS net-section provisions with material removed from the scenario
section by every intersecting hole, bore, housing, notch, kerf, and relief.
Use the parallel-to-grain tension provision and matching adjusted `Ft` only
when the resultant section force is along the scenario's longitudinal grain axis.
Where an Appendix E fastener-group equation is proposed, first show that its
group geometry and loading assumptions fit this exact connection. The
repository's net-tension helper is a reference calculation, not a finished
section check.

**Gates:** one reconciled finished cut/axis inventory for the scenario; exact
net sections at all critical planes; a specified conditional grain direction;
applicable scenario grade and adjustments; and fresh signed axial force and
moment. No current demand is available.

### Tension perpendicular to grain and splitting

**Criteria:** `supplemental_EC5_splitting` and the relevant sections of
`sampled_net_member`.

The NDS tension-perpendicular-to-grain provision is an avoidance/reinforcement
provision; it does not supply a general sawn-lumber `Ft⊥` value for these solid
wood blocks. Cross-grain separation, prying, and opening must be identified
from current signed actions before a specific method can be applied. The
adopted supplemental EC5 splitting question remains separate from parallel
row/group tear-out. Its exact edition, clause, inputs, factors, and fit to each
current solid-wood group still need to be established, or replaced by an
equivalent supported method. A BSI record for the standard alone is not that
method. No 4D/7D geometry screen or conditional grain frame closes splitting.

**Disposition:** unresolved method and demand; criterion remains `pending`.

### Shear at cuts and member connections

**Criteria:** `sampled_net_member`, `base_end_notch_shear`, and
`taper_sampled_rectangular_shear_torsion`.

Use the current NDS shear provisions for the specified member scenario and
shear direction, including the member-at-connection provision where applicable.
The March 2026 errata to NDS 2024 corrects shear cross-references to §3.4.4.1
and identifies cases for its shear reduction factor, including non-prismatic
members, notches, and members at connections. Apply the provision and factor only after
classifying the scenario member, load, and cut condition under the current text.
Do not transfer an unbored rectangular-section result to a section with a bore
or cut unless the chosen method includes it or its applicability is bounded.

**Gates:** bound finished taper/notch/bore geometry and local shear axes for
the scenario; member-specific reference `Fv` and adjustments from the matched
material table; and fresh shear demands. No current signed member shears
exist.

### Compression and stability

**Criteria:** `header_gross_full_length_stability`,
`sampled_member_stability`, and `sampled_net_member`.

Use NDS compression-member/column checks with matching adjusted `Fc`, specified
member length and end restraint, and both principal-axis stability conditions
in the scenario. Combine compression with bending when the same case produces
both actions. The prior angle-frame restraint and prior candidate checks do
not transfer to the reviewed block candidate.

**Gates:** scenario-bound final member sections, unsupported lengths, and
restraints; accepted joint translational/rotational behavior; source-bound
scenario grade and species group; applicable adjustments; and fresh six-case
actions. These inputs are not complete.

### Wood-face and washer bearing

**Criteria:** `base_bearing_average`,
`base_bearing_quarter_area_sensitivity`, `floor_rail_wood_bearing`, and
`washer_bearing`.

For wood-face compression parallel or perpendicular to grain, use the NDS
bearing provisions with net active bearing area and the matching adjusted
parallel-compression `Fc` or perpendicular-compression `Fc⊥` value. Where the
compression direction is oblique to grain, use the applicable angle-to-grain
provision only after the member frame is established. Model contact opening
and pressure distribution separately; an NDS resistance value does not set the
active face or pressure field. Retain the adopted quarter-area sensitivity as
its own pending criterion.

For bolt-to-wood dowel bearing (`local_parallel`), keep the NDS Chapter 12
dowel-bearing/yield method distinct from member-face bearing under NDS §3.10.
The current reference helper supplies at most one wood-bearing input; it does
not establish bolt/group resistance, load share, or complete-joint capacity.

**Gates:** specified contact graph and conditional member/grain directions,
active-face area, washer footprint and cuts, applicable matched design-value
table and adjustments, and fresh signed normal/bolt actions. Current contact
forces and pressures are not available.

### Torsion

**Criteria:** `taper_sampled_rectangular_shear_torsion` and
`sampled_net_member`.

The sources reviewed provide NDS member shear provisions and shear-parallel
wood design values, but this screen found no accepted member torsion method
for the candidate's orthotropic sections with bores/cuts. `Fv` is not adopted
here as a stand-alone torsional resistance. A future method must resolve the
scenario section and openings, orthotropic shear directions, material basis,
and current torque; an unbored rectangular formula does not close cut stations.

**Disposition:** unresolved method and demand; criterion remains `pending`.

## Grade, property, and grain gates

The current grade-disposition record assigns no actual grade or design values.
Its four proposed 4×6 rips are two `center_principal_cleat` pieces (5 mm rip to
83.9 × 139.7 mm) and two `knee_outer_*_inner_frame_block` pieces (6.35 mm rip
to 88.9 × 133.35 mm). These are proposed nonstandard final sections, not
physical measurements.

NIST PS 20-25 §7.3.7 states that ripping/remanufacture negates the original
product's grade, grade mark, and design values; the mark is removed. Sections
6.1.6 and 8.1.4 describe inspection service for nonstandard sizes under
applicable certified grading rules; those provisions do not assign a grade to
these rips. Thus none of these four blocks may inherit the source 4×6 value
set.

A named hypothetical scenario may assume an independently assigned final-piece
grade without asserting that physical inspection or regrade occurred. It is
analyzable only when it identifies an eligible certified grading-rule route
and specifies the assumed final-piece grade (or no-grade case), species or
species group, product, final size, seasoning/moisture and treatment
conditions, and applicable rule limits. It must also identify the exact
matching NDS-2024 Supplement table entry and every applicable adjustment,
limit, and assumption. A named grade alone, or the PS 20 inspection route, does not
establish certified-rule eligibility or authorize a design value. No complete
scenario or actual piece-level grade disposition is recorded here; WJ-11
receiving and regrading evidence may remain blank as conditions. The two
center blocks also lack per-body shape fingerprints in the pinned source
record.

The material-frame maps are conditional geometry/material scenarios, not
observations of delivered boards. An analytical scenario must bind each timber
ID to a specified longitudinal grain axis and specify or bound the required
transverse frame for orthotropic analysis; the unresolved ring orientations
may be carried as separate named cases. The source/model `DF-L No. 2` label
may define a conditional analytical case only with specified source/product
identity and table eligibility; it is not a delivered species/grade record.
The 20 un-ripped frame members likewise lack delivered species, grade,
treatment, moisture, and receiving evidence, which may remain blank for MVP-E
scenarios. No design value is assigned to any member by this screen.

For an eligible source-bound sawn-lumber scenario, the candidate property path
is one matched edition of ANSI/AWC NDS-2024 and its 2024 Supplement, selecting
the exact applicable species/grade/product-size table entry and recording all
NDS adjustments and limits. The supplement publishes `Fb`, `Ft`, `Fv`, `Fc`,
`Fc⊥`, and stiffness values by applicable product/grade. WWPA explains that
its published Western softwood values use ASTM property-establishment bases;
those values support a scenario only after exact product/species/grade
eligibility and table matching are specified. ASTM D245/D1990/D2555 explain
grade/value establishment; they do not grade these individual post-rip pieces
or establish WJ-11 disposition of delivered pieces.

## Source register

All web sources below were accessed 2026-09-27. No capacities or numerical
design values were taken from them.

- [ANSI/AWC NDS-2024, AWC standard page](https://awc.org/resources/2024-nds/):
  ANSI approval date 2023-10-16; current cited edition is 2024. AWC advertises
  view-only access. The page reserves search, printing, and zoom for the
  purchased PDF; this note does not describe the complete standard as a free
  unrestricted download.
- [2024 NDS Supplement, AWC](https://awc.org/resources/2024-nds-supplement/):
  design values for sawn lumber, glulam, and round timber; AWC says its values
  and design provisions must be used as a matching edition.
- [AWC NDS updates and errata index](https://awc.org/topic/nds/): the
  March 2026 2024 NDS errata/addenda file `03.23.26` was consulted for §3.4
  shear references and connection/notch applicability.
  Direct file: <https://awc.org/wp-content/uploads/2026/03/2024-NDS-Errata-and-Addenda-03.23.26.pdf>
- [WWPA design values](https://www.wwpa.org/western-lumber/design-and-application/design-values/):
  property meanings, applicability to Western softwood, and named ASTM bases
  D245, D2555, and D1990.
- [ASTM D245-25](https://doi.org/10.1520/D0245-25), [D1990-26a](https://doi.org/10.1520/D1990-26A),
  and [D2555-17a(2024)e1](https://doi.org/10.1520/D2555-17AR24E01): ASTM
  records identified these editions as active on the access date. These
  establish allowable-property methods, not a grade for this stock.
- [NIST Voluntary Product Standard PS 20-25](https://www.nist.gov/document/ps-20-25-final):
  January 2025; §7.3.7 says remanufacture negates the original grade, mark,
  and design values; §§6.1.6 and 8.1.4 address inspection service for
  nonstandard sizes under certified grading rules, but do not themselves
  assign a grade to a piece.
- The source-bound [`wood-limit-state-basis.md`](../../../wood-limit-state-basis.md)
  is a repository snapshot that records the BSI listing for
  BS EN 1995-1-1:2004+A2:2014 as current, under review. BSI's live catalog
  also lists
  [BS EN 1995-1-1:2025](https://knowledge.bsigroup.com/products/eurocode-5-design-of-timber-structures-general-rules-and-rules-for-buildings)
  as current, under review, published 2025-11-30; both catalog records were
  checked 2026-09-27. No EC5 edition or National Annex is adopted here. The
  record and listings do not supply the missing exact splitting clause or
  prove applicability.

## Repository inputs and hashes

The SHA-256 values below identify exact repository file snapshots consumed for
the initial attempt01 screen. They do not assert that the files remain current.
For this scope correction, the active plan was rechecked on 2026-09-27 at
SHA-256 `b634e27775949aaae0ca04ba863869bafedf6fd340e7627939c48f7dd72a6dca`;
the earlier plan hash below remains the version consumed by the initial screen.
The evaluation-resume paths below are relative to
`docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/`.

- `AGENTS.md`
  SHA-256: `672203b929d51d340d39d770e71dd43b019794ea33172bc9f4f7be469fc20536`
- `docs/wood-joints-mvp/next-mvp-plan.md`
  SHA-256: `02b7aec8f62f00dd20b32695533ecba579ff9d6fd5ff7b3105a1e714c2752db0`
- `docs/wood-joints-mvp/criteria-method-map.md`
  SHA-256: `2ab30c154d75306cb83c88fdde98f7af8082b3c57089a9fdf587c5b3b9818182`
- `docs/wood-joints-mvp/criteria.json`
  SHA-256: `fd1df5f106b944d21bc237d0ff789eb30437640ce81cb3e059c7e21f3a531784`
- `docs/wood-joints-mvp/wood-limit-state-basis.md`
  SHA-256: `1110e664a88f704773a463e83a2aeac3954b978048d811e4bff1effa55aa7c2e`
- `current-block-material-frame-map-attempt02/README.md`
  SHA-256: `dd25a3c19f88238cfff4697c34b1cc00916f5b411636366f5d0fb26951e943d2`
- `current-block-material-frame-map-attempt02/material-frame-map.json`
  SHA-256: `8705b8f100a2d3355c236fc19e6798bb7ad4862ba2d51826cf63a88db1285480`
- `current-frame-timber-material-frame-map-attempt01/README.md`
  SHA-256: `4c465d77dfd069f5fa69fbcc729ebe18cee42ece6c812d0c3ba059fd045d8e1d`
- `current-frame-timber-material-frame-map-attempt01/current-frame-timber-material-frame-map.json`
  SHA-256: `f867b4926ed23c9f356005c134778e138c8b1230547f0b69be7c3f9bc2a42409`
- `current-timber-grade-disposition-attempt01/README.md`
  SHA-256: `7266a00f72dbe46ac6917cfc7ee3588f85ca5d42d9daf4a916ff6fa529a873b0`
- `current-timber-grade-disposition-attempt01/grade-disposition.json`
  SHA-256: `c0e5c0bb9a32403a6fe047a3b995667f2d35df81b1333a68f773c318ed560e86`

## Limits and checks

This is not a capacity calculation, complete connection design, accepted
resistance contract, or candidate pass. No demand was inferred from historical
or unit-load cases. All applicable criteria remain pending until method,
geometry, material/grain, and fresh demand inputs are bound.

Read-only checks performed: source/version review and SHA-256 calculation for
the repository inputs listed above. No tests, CAD, solver, or physical work
were run. I changed no geometry, solver code, plan, ledger, or criteria.
