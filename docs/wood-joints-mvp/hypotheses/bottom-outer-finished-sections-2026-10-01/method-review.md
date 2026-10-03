# Bottom-outer finished-section method review

This note limits the resistance methods available for the CLEAT, RAIL, and
SIDE finished sections at the four bolt-grain stations. The intended source
actions include the complete native point-action boundary and nodal body
loads. This is a method review only: it adopts no resistance, member grade,
service factor, or joint disposition.

## Sources checked

| Source | Provisions inspected | Local SHA-256 |
| --- | --- | --- |
| AWC 2024 NDS Appendix, September 11 version | Appendix E.1–E.5, printed pp.174–175 (PDF pp.9–10) | `1fa2bcf52803b1bbed8ea30cf13551dd5f76c90bf110ac475b401f81d116ec31` |
| AWC 2024 NDS Chapter 11, September 11 version | §§11.1.2–.3, printed p.70 (PDF p.2) | `45a3d78de1a4fba573589be0fc776e37bd581e4cedec24e38d63856161092d33` |
| AWC 2024 NDS Chapter 2 | §§2.1.1–.2, printed p.12 (PDF p.2) | `6bb62f3560ab5bcdbed297cd03bba560f20882a638ee591c0c97013f7c075100` |
| AWC 2024 NDS Supplement, Chapter 4 reference values | Table 4A, DF-L No. 2 row, for a conditional property scenario only | `1f65975633f111c308944c470b6cc10e9207b6c45e8a0804b8bdec3378bbc71b` |

The local official-source cache contains Chapter 11, Chapter 2, the Appendix,
and the Chapter 4 Supplement, but not a Chapter 3 PDF. Chapter 11 §11.1.2
requires member checks including the referenced NDS §3.1.2 and §3.1.3, and
requires local stresses at multiple-fastener connections to be checked by
engineering mechanics; it calls Appendix E one method. This review relies on
that pinned direction and on the directly inspected Appendix E text. It does
not claim an independent page-by-page review of Chapter 3.

## What the pinned methods support

Appendix E is expressly a nonmandatory method for a single fastener or a
closely spaced fastener group loaded parallel to grain (E.1). It identifies
net-section failure and tear-out from local stresses as possible limits, not
an exhaustive design for every stress mode.

For a demonstrated grain-parallel net-tension demand through the complete
critical section, E.2-1 provides the adjusted net-section tension reference
`Z′NT = Ft′ Anet`, with `Anet` defined by NDS §3.1.2. Thus the geometry
producer may report the actual net wood area, the connected or disconnected
regions at the cut, and a conditional whole-section parallel-tension
comparison if the corresponding section action and adjusted `Ft′` are
established. This is one limit state only. A net-area result does not establish
the load carried by each strip, a bending capacity, a splitting capacity, or a
complete member/joint pass.

E.3 concerns tear-out of a fastener or a row using the minimum shear area and
the stated row/end geometry. Its multiple-fastener expression assumes two
shear lines, and E.3.3 describes a triangular shear-stress distribution
between fasteners. E.3.4 calls verification limited. E.4 combines bounding-row
tear-out with a specified critical group net section; E.4.1 requires examining
different critical group areas for nonuniform row spacing. These provisions
do not authorize treating every ligament at a bore plane as a separate
parallel fastener row, or summing unrelated strips as a group-tear-out path.
Nor do they provide a general splitting check for transverse tension or an
oblique complete-joint wrench. Chapter 11 §11.1.3 separately requires
appropriate engineering procedures or tests for eccentric connections that
induce tension perpendicular to grain.

The Chapter 4 Supplement's DF-L No. 2 values can serve as a declared
conditional property basis. A calculation must still identify the applicable
member adjustment factors and the service assumptions; setting a factor to
1.0 is a scenario, not an observation about this structure. Neither the
conditional table row nor force fidelity qualifies actual stock, grade,
finished cuts, or resistance.

## Disconnected cut regions and section wrenches

At the rail-bore center, the proposed transverse bore leaves two R-directed
strips on the grain-normal section. At the side-bore center, the two
through-holes leave three Q-directed strips. These are cross-section regions
of the same three-dimensional member; they are not independent whole
members. Their physical connection elsewhere does not, by itself, prove equal
strain or area-proportional force sharing at the cut.

A source-derived six-component wrench and exact section geometry establish
the resultant and its equilibrium at the stated datum. They do not establish
tractions or axial force/moment shares on the separate strips. Therefore do
not assign each strip `N × Ai / Anet`, calculate one common `Fb′ × Anet`
capacity, or convert `N`, `M`, and net area directly into a local stress
without stating and validating the needed compatibility model. For bending,
area is not the resisting section property; any use of section modulus and a
combined axial/bending check also depends on a justified strain/load
distribution at this perforated station. Geometry may report each region's
area, centroid, and section-property inputs, but those alone are not a
resistance calculation.

The source point-action reconstruction, including body loads, can support
same-state section force and moment equilibrium. It does not integrate
finished-section FE tractions. Near a bore where source actions enter or
leave, retain the source-force jump and bracket the section on both sides;
do not spread a point action over the net area or infer a local stress peak
from a resultant.

## Closure path

There is a narrow Appendix E path if a cut is shown to carry grain-parallel
axial tension without an unaccounted eccentricity: compare that complete-cut
force with `Ft′ Anet` under an explicitly declared property/service scenario,
then separately check all other applicable actions and failure modes. If the
same-state wrench includes material bending, shear, torsion, or perpendicular
grain tension—as must be retained unless proved negligible—the net-tension
comparison alone cannot close the section.

To resolve the disconnected regions, use either (1) a source-bound
three-dimensional mechanics solution on the finished CLEAT/RAIL/SIDE
geometry, with the same external point actions and distributed body loads,
that recovers compatible stresses/tractions and checks mesh/section
equilibrium, or (2) a separately justified mechanical load-sharing model
that traces transfer between each region and the rest of the member and
balances force and moment at control volumes bracketing the bore. Then check
the resulting regional and complete-section actions against applicable
adjusted tension, bending, shear, bearing, and splitting criteria. The
current cut resultants alone do not supply this regional transfer. If no
such compatibility/equilibrium method is established, retain the result as
demands plus area/region geometry and leave resistance open.

No capacity, strength pass/fail, physical inspection, or fabrication
conclusion follows from this note.
