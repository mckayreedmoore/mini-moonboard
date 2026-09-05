# 2×8 feasibility: smaller rim, unresolved connections

**Comparison candidate, not a build recommendation.** The 2×8 is worth testing
as a lower-material alternative, but a smaller timber section and a buildable
complete frame are different questions. The plywood reference and published
2×10/2×12 candidates remain comparison records, not approved designs.

## Stock dimensions and section comparison

The [American Softwood Lumber Standard PS 20-25, Table 3](https://alsc.org/uploaded/PS%2020-25%20Final.pdf)
lists dry dressed dimension lumber as 1½ inches thick, with widths of 7¼,
9¼ and 11¼ inches for nominal 2×8, 2×10 and 2×12 respectively. The CAD uses
exact inch conversions below; the standard's metric entries are rounded.
These dimensions do not select a species, grade, moisture condition or strength.

For equal-length, homogeneous rectangular side rims at the **same assumed E**:

| Quantity | Plywood reference | 2×8 | 2×10 | 2×12 |
| --- | ---: | ---: | ---: | ---: |
| Thickness × full depth, mm | 38.1 × 322.8 | 38.1 × 184.15 | 38.1 × 234.95 | 38.1 × 285.75 |
| Normal bending EI, relative to plywood | 100% | 18.57% | 38.56% | 69.37% |
| Lateral bending EI / gross volume, relative to plywood | 100% | 57.05% | 72.79% | 88.52% |
| Extreme-fibre stress at equal normal moment | 1.00× | 3.07× | 1.89× | 1.28× |

These follow `I_normal = b h³ / 12`, `I_lateral = h b³ / 12`, and
`Z_normal = b h² / 6`. The 2×8 has 48.15% of the 2×10's normal EI and
26.76% of the 2×12's. The volume column concerns the side rims only, not the
whole assembly or its mass. Neither EI nor stress ratios are capacity ratings.
Do not divide the published whole-frame displacement by these ratios: panels,
backing, legs and joints participate in the complete frame's response.

Actual wood is not the equal-property isotropic material assumed by this screen.
Grain direction, knots, moisture and other material differences matter; see the
[USDA Wood Handbook, mechanical properties](https://research.fs.usda.gov/treesearch/62244).
No higher lumber modulus is assumed merely to compensate for reducing depth.

## Geometry gate before a complete candidate

Reducing the full depth to 184.15 mm leaves the rear datum at N=166.15 mm.
The existing front backing occupies N=0–38.1 mm and the 88.9 mm-deep rear
crossmembers occupy N=77.25–166.15 mm. The intervening normal ribs would be
only **39.15 mm long**, versus 89.95 mm for 2×10 and 140.75 mm for 2×12.
That is a connection-packaging constraint, not simply a stiffness reduction.

An isolated CAD check of the unchanged connection layout found 65 individually
valid solids but **28 unintended part collisions**: 16 climbing-panel/angle and
12 backing/angle intersections. Twelve rib-front screws exit their intended
rib, and twelve second rib bolts miss the rib. The 80 mm angle leaf reaches
N=−2.75 mm, through the backing and into the climbing panel; its second rib
bolt lies at N=17.25 mm, before the rib begins. The 88.9 mm front screw would
extend 11.65 mm beyond the rib into the rear crossmember.

The unchanged stack requires at least `18 + 38.1 + 88.9 + 80 = 225 mm`
full depth just to keep that angle leaf behind the front backing, before any
additional wood edge-distance or tool allowance. This is **not** a general
225 mm minimum frame depth. Rotating a rear 2×4 to occupy 38.1 rather than
88.9 mm in N would regain 50.8 mm, but changes its bending orientation and
requires new angles, bolt lengths and structural checks.

The existing rib-angle connection therefore cannot be inherited and labelled
valid without new part, bore, receiving-material, socket and bolt-removal checks.
A complete 2×8 viewer and purchase/cut schedule should wait for a revised
connection architecture. Shorter bolts alone do not establish sufficient wood
edge distances, bearing or splitting capacity. The glued two-layer plywood
legs remain 38.1 mm thick; this candidate does not replace them with 2×8 lumber.

## Smallest useful numerical comparison

A **timber-only, ideal-bonded 2×8 counterfactual** can answer whether the smaller
wood geometry is worth developing before spending effort on new connectors.
Use the same six historical resultant vectors, five row-12 target positions,
E=7000 MPa, nu=0.3, fixed floor and 60/40 mm meshes as the larger hybrids.
Keep equilibrium, positive-Jacobian and loaded-node sampling checks identical.
This deliberately replaces unresolved connections with perfect timber bonds;
it cannot demonstrate that such connections can be built or carry the loads.

That comparison is now solved: six historical cases at each of two meshes,
**12 completed cases**, with [published records and raw DAT outputs](../fea/results/hybrid/2x8/).
The downward 1.2 kN case gives 0.84146 mm at the 60 mm mesh (62,601 nodes)
and 0.83925 mm at the 40 mm mesh (125,420 nodes), a 0.26% change. The accepted
meshes have positive minimum Jacobians of 2370.963 and 686.391 respectively.
The 40 mm mesh initially produced element-quality warnings; high-order
optimization recovered a positive final minimum Jacobian before the solve.
Force and moment equilibrium are audited from the actual deck and DAT output.
This is a two-mesh numerical check, not proof of stress convergence or safety.

| Candidate | 1.2 kN downward, 40 mm mesh | Relative to 2×12 |
| --- | ---: | ---: |
| 2×8 timber-only counterfactual | 0.83925 mm | 2.16× |
| 2×10 ideal-bonded candidate | 0.54483 mm | 1.40× |
| 2×12 ideal-bonded candidate | 0.38900 mm | 1.00× |

These are maximum displacement magnitudes **among the five loaded nodes**,
not the maximum anywhere in the model. All three bulk models omit steel and
fastener stiffness, but only the 2×8 lacks a non-colliding nominal connection
layout. Its higher displacement shows a stiffness tradeoff, not an allowable
deflection failure. No selected material strength or joint capacity is tested.

In separate stability calculations, explicitly omit the unresolved 2×8 angles
instead of crediting their mass at colliding locations. Label that timber-only
inventory separately from the wood-plus-angle inventories of the larger
candidates. Reduced dead weight can improve handling while worsening tipping;
report actual mass/centroid and support polygon, not just section savings.

## Applying the one-person weight decisions

The intended user limit is **250 lb (113.4 kg), one person**. The **300 lb
(136.1 kg)** case is a sensitivity, not an increased user rating. Their static
weights are approximately 1112.06 N and 1334.47 N using standard gravity.

For the already solved *linear, fixed-floor, no-gravity* downward model, scaling
the complete load vector by 0.9267 or 1.1121 relative to 1200 N also scales its
displacements and reactions. This is algebraic reuse of a linear solution, not
a new solve. At the same location and force direction, 300 lb produces 20%
more incremental response than 250 lb. It does not follow that tipping margin,
joint capacity or required footprint changes by 20%: dead weight stays fixed,
and real contacts can lift or slip.

Applying those factors to the 40 mm downward results gives:

| Candidate | 250 lb static weight | 300 lb static weight |
| --- | ---: | ---: |
| 2×8 timber-only counterfactual | 0.77774 mm | 0.93329 mm |
| 2×10 ideal-bonded candidate | 0.50490 mm | 0.60588 mm |
| 2×12 ideal-bonded candidate | 0.36049 mm | 0.43259 mm |

This table is **linear rescaling, not additional FEA runs**; the same five-node
maximum definition applies. It answers incremental stiffness under a changed
downward resultant, not whether dynamic climbing at either weight is safe.

Keep historical 1.2 kN evidence unchanged. Treat doubled body weight, horizontal
forces, hold stand-off, reduced dead mass and lateral positions as separately
labelled sensitivities, not sourced dynamic amplification or a complete safety
envelope. Rescale only the components intended to scale: a fixed 300 N lateral
probe must not accidentally become a weight-scaled probe. New locations or
directions require corresponding load cases, not scaling a scalar maximum.

The next selection gate is combined: viable connection geometry, acceptable
unanchored stability under a justified envelope, and connection-aware structural
checks. A low displacement alone is insufficient to choose 2×8 or a smaller rim.
