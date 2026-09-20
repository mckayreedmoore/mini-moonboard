# Six rail-to-center duties: factory through-bolt bracket shortlist

**Bounded source screen, 2026-09-20.** Three rails per side need a new center
attachment after the inner cuts at X = ±120 mm. The original rails are 1.5 in
(38.1 mm) thick. A separate one-piece profiled-rail trial retains a full
90.4748-mm (3.562-in) section only in a 63.5-mm inner contact band on each
*bottom* rail; it has not established that section for all six rails. See the
[six-rail cut](hardware_first_center_hybrid_rails.md) and
[profiled bottom-rail screen](hardware_first_center_rail_relief.md). The raised
one-piece header is a separate receiver. Retail listings identify products,
not local stock or a compatible installed joint.

### Simpson A66 — conditional for the original 1.5-in rail

[Home Depot #100375146](https://www.homedepot.com/p/100375146) lists exact
model A66, with 5-7/8 × 5-7/8-in legs and a 1-1/2-in bend length.
[Simpson C-C-2026 p. 314][simpson-catalog] specifies **two 3/8-in structural
through-bolts per leg** (four total). Its A66 table states no model-specific
minimum wood thickness, so the original 1.5-in rail has no stated thickness
exclusion. Factory hole positions, timber edge/end distances, bolt stacks
and flange fit still need proof. Thicker wood is also a conditional fit.

**Action coverage:** the bolt-option F1/F2 load cells are dashes. No published
A66 bolt-option load can be assigned to either direction. Nailed-angle values
cannot transfer; separation, both shear senses, moment, mixed action and
slip are unestablished for this joint.

### Simpson HL33 — no for 1.5 in; conditional for at least 3.5 in

[Home Depot #205227144](https://www.homedepot.com/p/205227144) lists exact
model HL33, with 3-1/4-in leg reach and 2-1/2-in bend length.
[Simpson C-C-2026 p. 315][simpson-catalog] specifies **one 1/2-in structural
through-bolt per leg** (two total), ASTM A307 Grade A or better. The angle
must be centered on a face at least 3-1/4 in wide; the `3`/`5` series needs
**3-1/2-in minimum actual wood thickness**. Both the profiled rail at its
bolt location and the header must independently meet that minimum.

**Action coverage:** catalog DF/SP uplift 740 lb and F1 1,040 lb have the
`160` wind/earthquake-duration label. Simpson calls for reduction where
other loads govern but gives no separate HL33 ordinary-duration table.
F1 in both senses requires angles on both sides; one angle does not cover
it. Other shear, joint moment, mixed action and slip are unestablished.

### MiTek B66 / retail UB66 — no for 1.5 in; conditional for at least 3 in

[Home Depot #313507617](https://www.homedepot.com/p/313507617) lists UB66.
The [MiTek retail cross-reference][mitek-crosswalk] maps UB66 to factory B66,
a 1-1/2-in-wide brace with 6-in legs. The [MiTek B-series sheet][mitek-sheet]
and [ESR-3455 Table 3/Figure 3][mitek-report] specify **two 3/8-in
through-bolts per leg** (four total), ASTM A307 Grade A or better, and
**3-in minimum actual wood thickness**. A 3.5-in one-piece rail exceeds
that minimum; its exact bolt region and the header still need checks.

**Action coverage:** B66 F1/F2 values of 710/335 lb apply to the specified
single brace at `C_D = 1.6` only. The report bars applying or adjusting
them to other durations. F1 in both senses requires braces on both sides.
No ordinary-duration or complete rail-joint value follows; separation,
other shear/moment combinations and slip remain unresolved.
The same ESR-3455 identifies B corner-brace steel as ASTM A653 SS Grade 40
(Table 29) and sets a 0.099-in minimum base-steel thickness for No. 12 gage
(§3.29.1). These are conditional inputs for a **separate** formed-angle
assessment, not permission to transfer the `C_D = 1.6` product loads or
assume bend, local-buckling, bolt-bearing, and wood resistance are checked.

[simpson-catalog]: https://ssttoolbox.widen.net/content/orplhjaqw1/original/C-C-2026.pdf?download=true
[mitek-crosswalk]: https://images.thdstatic.com/catalog/pdfImages/2f/2f1009db-047c-4da8-a283-bcda2c494ebe.pdf
[mitek-sheet]: https://www.mitek-us.com/wp-content/uploads/2020/12/B_-BL.pdf
[mitek-report]: https://www.mitek-us.com/wp-content/uploads/files/pdf/Code%20Evaluation%20Reports/esrESR-3455.pdf

The Simpson catalog's general bolt instructions specify structural-quality
**through-bolts**; no cited source establishes a carriage-bolt substitution
for these poses, and lag screws are not through-bolts. No wood screws or nails
are used in the shortlisted *bolt configurations*. The A66 and HL33 listed
parts are exact catalog models. UB66 is MiTek's retail designation for B66,
not an inferred competing-brand substitution. The MiTek report's wood-grade,
bolt and installation conditions still apply. No published load number above
is assigned to a MoonBoard rail.

## One installed-face orientation screen

Consider each cut rail butting into a separately supported center/header
assembly, with one flange on an accessible **transverse side or rear face of
the rail** and the other on a perpendicular **header face**. This keeps the
rail through-bolt across its 1.5-in or profiled thickness, rather than along
its roughly 1-m length. The bracket must bridge the actual surfaces while
both flanges bear on solid wood. **Verdict: conditional as a layout concept,
no as an established attachment for any of the six duties.** The sources do
not establish six noncolliding flange seats, factory-hole centers on the
shortened/profiled timber, a full-width receiving header face, bolt-end and
washer/tool access, grain/edge/end distances, or a two-way force and moment
path. The profiled trial verifies a full-thickness *bottom-rail* band, not a
six-rail bracket layout. For a flange placed directly on the inner X-normal
rail end instead, the bolt would run along the roughly 1007–1010-mm rail:
**no** for that simple removable through-bolt pose, as already screened in
the [rail relief note](hardware_first_center_rail_relief.md).

No ordinary-duration six-joint rating is published for these installations.
Do not divide MiTek's `C_D = 1.6` figures, transfer Simpson's wind/uplift
figures or A66 nail values, multiply one bracket's rating by six, or infer a
moment rating from bolt count. The next design gate is a measured six-station
pose with delivered bracket geometry, complete removable bolt stacks and
direction-specific demands. This document makes no purchase, drilling or
structural-acceptance claim.
