# Hybrid frame: provisional load basis

Research checked 2026-09-05. **Analysis planning, not construction approval.**
This separates sourced requirements from project sensitivities; it does not
change the six historical cases in `mini_moonboard/stability.py` or reinterpret
the [published bonded-frame results](hybrid-frame-fea.md) as joint validation.

## What the primary sources establish

The [CWA specification](https://www.cwapro.org/file/secure/cwadesignpecfinal2022.pdf)
provides these relevant provisions:

- Table 1: 1.2 kN unroped-climber load.
- Sections 4.4 and 5.5: examine relevant surface locations and their load paths.
- Sections 4.5–4.7: minimum overturning factor 1.5; use dead load; do not count
  opposing live loads as ballast. For walls without protection anchors, place
  the utilization-capacity climber load at the worst location, or use the
  alternative 718 N/m² uniform load to maximize instability.
- Sections 3.2.4 and 4.5.4: route geometry and simultaneous utilization matter.
  The route definition uses 1.5 m spacing; a single-climber calculation alone
  does not establish compliant capacity for this approximately 2.44 m board.
- Section 5.3.1's 9° direction rule concerns protection anchors, not a general
  prescription for board-normal surface forces.
- Section 1.4 covers stationary, fixed-in-place structures, including temporary
  installations, but not specifically portable structures. Sections 4.2 and 8
  require applicable engineering methods and qualified review.

Applicability to our relocatable, unanchored frame therefore needs review.
The document's filename/copyright is not a newly issued code edition; it identifies
itself as the January 2009 first edition. Do not silently adopt its historical
building-code references as the current local code.

[BSI lists EN 12572-2:2017](https://knowledge.bsigroup.com/products/artificial-climbing-structures-safety-requirements-and-test-methods-for-bouldering-walls)
as current and under review. It covers bouldering-wall calculation and testing,
including surface impact and panel-insert resistance. The public overview is
not the full normative calculation/test procedure. No unverified EN force,
partial factor or acceptance threshold is imported into this project.

[Moon's Mini DIY product guidance](https://us.moonclimbing.com/products/mini-moonboard-2020-diy-kit)
excludes the supporting frame and says support requirements vary by installation.
Its commercial freestanding product is a separate steel system. Consequently,
the reference video's appearance and the DIY panel geometry do not establish
a load rating for our laminated-plywood/lumber frame.

## Recommended next computational envelope

These are **project-selected comparisons**, not prescribed dynamic loads or a
complete design envelope. Keep results in separately labelled groups.

| Group | Proposed calculation | Purpose / limitation |
| --- | --- | --- |
| Historical baseline | Existing 1.2 kN downward and six original cases, unchanged | Preserve comparison to plywood and both hybrids |
| Downward sensitivity | 1.2 and 2.4 kN downward | The 2× case is not a verified dynamic amplification or a two-user design approval |
| Horizontal sensitivity | Each downward level combined with 0 or 300 N horizontal force, toward/away from the climber and left/right | Explicit sensitivity, not a measured peak; include diagonal azimuths to find support-polygon edges |
| Legacy normals | Existing opposite 1.2 kN board-normal vectors | Retain their uplift failures separately; do not label them established governing use cases |
| Location sensitivity | Every main hold and kicker position, plus accessible top/side edges if those may be used | A centered five-node load can hide torsion and concentrated joint demand |
| Hold stand-off | 0, 50 and 100 mm from the climbing face along its outward normal | Guesses for leverage sensitivity, not measurements of the 2025 holds or a guaranteed upper bound |
| Dead-load sensitivity | Current inventory mass/centroid; a clearly labelled 20% lower mass at the same centroid | Numerical sensitivity only, not a statistical material bound; later replace with component masses and positions |

Run each applied resultant independently. Do not apply the full climber force
at every hold simultaneously. For concentrated-load FEA, spread a single hold
resultant over a physical contact/attachment patch, not an arbitrary singular
node. Then add representative simultaneous hand/foot forces with their net
force **and couple** preserved; equal sharing across five top holds is not that
model. Movement can change the whole-body resultant, while opposing hand/foot
forces can create local joint demands despite a modest net force.

For footprint ranking, use the actual floor contact polygon, gravity and
unilateral contact: no floor tensile reactions or anchoring credit. Report
overturning separately from required friction. Friction remains unknown;
a low calculated demand is not a sliding pass. A 1.5 moment screen is not a
complete load-combination implementation. Three-dimensional equilibrium alone
also cannot determine unique individual foot reactions without compliance.

## Inputs that still require a human decision or measurement

- Maximum intended user mass, simultaneous-user policy, dynamic moves,
  side/top-edge use and any foreseeable non-climbing loads. Height alone does
  not establish weight or force. Qualified review must reconcile intended
  use with the applicable utilization and load-combination rules.
- Actual floor/foot interface, floor capacity and levelness, measured component
  weights/centroids, and installed hold contact offsets. No room-clearance or
  pad dimensions are needed for this numerical comparison; the pad remains a
  separate excluded element, not ballast or a support.
- Selected lumber grade/species, plywood construction, moisture and glue
  specification; manufacturer-rated joint hardware and installation details.
- Governing standard/code and qualified structural reviewer; justified dynamic
  and lateral envelope, fatigue, local hold/T-nut loads, and a controlled
  physical verification procedure before use.

**Decision gate:** compare footprint options now, but do not choose ballast,
declare a final minimum footprint, or soften the exploratory failures merely
to obtain a pass. Real contact and connection-aware analysis follows selection
of a defensible load basis and material/joint properties.
