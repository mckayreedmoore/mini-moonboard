# Shallow-frame development: next five steps

The next candidate is a **2×8 rim with reoriented rear 2×4 crossmembers**.
This is a comparison milestone, not authorization to build or climb. Keep the
plywood, 2×10, 2×12 and original timber-only 2×8 results unchanged so the cost
of each geometric change remains visible. Intended use remains one climber,
250 lb maximum, with 300 lb as a separate sensitivity rather than a rating.

## 1. Make the shallow connection stack geometrically viable

Rotate the rear crossmembers from 88.9 mm to 38.1 mm depth normal to the board,
recovering 50.8 mm within the 184.15 mm overall rim depth. Redetail the normal
ribs, angles, bolts and screws around that orientation rather than shortening
fasteners in the colliding legacy layout. Retain the climbing-face datums,
LED/hold positions, laminated 38.1 mm plywood legs and no-anchor constraint.

**Acceptance:** valid solids, intended bearing/contact, no unintended part or
fastener collisions, receiving-material checks, full floor bearing, and clear
socket/bolt-removal and lighting envelopes. Publish exact nominal geometry and
remaining hardware assumptions. Passing this gate does not establish timber
edge-distance adequacy or connector capacity.

## 2. Measure the stiffness cost against all four references

Use the existing Docker/Gmsh/CalculiX workflow and historical six load vectors,
five loaded hold positions, material assumptions and two mesh settings. Keep
the old unrotated 2×8 counterfactual distinct from the revised candidate.
Include the plywood-only result, **0.36846 mm** in the 1.2 kN downward,
40 mm-mesh case, in the comparison. Report 250/300 lb linear rescaling separately
from new solver runs.

**Acceptance:** positive final element Jacobians, complete finite results,
force and moment equilibrium, source/deck/result hashes, and mesh-sensitivity
reporting. Name the displacement measure: maximum among five loaded nodes,
not whole-model maximum. Perfectly bonded, fixed-floor results remain stiffness
comparisons, not joint, uplift, buckling or failure validation.

### Why rotating the rear member is not a free change

For a rear member spanning X, its cross-section is in the uphill S and
board-normal N directions. The unrotated member is 38.1 mm in S by 88.9 mm in N;
rotation exchanges those dimensions. With the same assumed elastic modulus:

| Isolated rear-member quantity | Rotated / unrotated |
| --- | ---: |
| Bending stiffness for deflection normal to the board, about S | `(38.1 / 88.9)² = 0.1837` |
| Bending stiffness for uphill/in-plane deflection, about N | `(88.9 / 38.1)² = 5.4444` |
| Gross section area and equal-length mass | `1.0` |

These are rectangular-section calculations using `I = b h³ / 12`, not predicted
whole-frame displacement ratios. The rotation reduces isolated normal bending
stiffness by about 82%, while increasing the perpendicular bending stiffness.
Longer ribs, changed connection eccentricity, bearing faces and panel/grid load
sharing also change the assembly response. Equal member volume does not imply
equal assembly mass or centre of gravity after those changes.

Do not silently rotate an orthotropic material's grain away from the actual
member axis. Grain remains along X; actual species, grade, moisture and radial/
tangential directions are not resolved by the isotropic screen. Wood-property
variability, grain and growth-feature effects are discussed in the
[USDA Wood Handbook, Chapter 5](https://research.fs.usda.gov/treesearch/62244).

## 3. Recompute unanchored stability from the new inventory

Use the revised CAD mass, centre of gravity and actual floor-contact polygon.
Repeat the [one-person envelope](user-load-envelope.md): both user weights,
hold projections, reduced-mass sensitivity and horizontal directions, with
legacy normal-force cases retained separately. Compare any needed footprint
changes as explicitly modelled alternatives, not extra reach credited without
the corresponding members and mass.

**Acceptance:** report governing positions and tipping edges, restoring factors,
uplift and friction demand without suppressing failing cases. The 1.5 project
moment screen is not complete structural approval, and unknown floor friction
is not a sliding pass. No anchors, pad support or unspecified ballast are credited.

## 4. Select a buildable connection strategy and establish its limits

Follow the [joint development plan](hybrid-joint-next-steps.md). Prioritize the
leg bolt group and rib-to-front-backing interface; preserve detachable rear
members. Replace generic end-grain withdrawal assumptions with a justified
side-grain/bearing detail or an applicable tested product provision. Select
actual products or engineered fabricated details before claiming a purchase
schedule. Record grain axes, timber/plywood grades, adhesive and fastener data.

**Acceptance:** explicit load paths and demand-versus-resistance entries, with
unresolved capacities marked unresolved. Where calibrated connection properties
are unavailable, publish bounded sensitivity instead of invented stiffness.
A later connection-aware model must release the old perfect bonds and allow
floor lift-off; fixed-floor bulk FEA cannot substitute for it.

## 5. Publish a reviewed decision package

Publish the revised CAD/viewer, dual-unit parts and nominal fastener schedules,
comparative stiffness/stability results, and a clear retain/reject/redesign
recommendation. Independently review geometry, calculations and software tests;
commit and push coherent increments so the GitHub record stays inspectable.
Keep the default/reference model distinct from experimental candidates.

**Completion point for this iteration:** an auditable shallow-frame candidate
and evidence-backed comparison, or a documented geometric/structural reason to
retain a deeper rim. Going below 2×8 is a subsequent decision, not an assumed
benefit: demonstrate room for connections and acceptable load-path/stability
behavior before another reduction.

**Deferred construction gates:** qualified review of the governing load basis,
real material and joint capacities, floor contact/friction, assembly stability,
and a controlled physical verification procedure. No result in this plan
establishes a safe user rating or permission to climb the frame.
