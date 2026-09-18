# Support-leg comparison for a 150 lb climber

The member calculations do not establish a need to increase the legs from
single 2×6 to single 2×8 for a 150 lb climber. The specified 2×6 timber passes
the checked member cases. The existing four-bolt attachment is not established
as sufficient, and the larger six-bolt candidate is not automatically qualified
by its larger stock.

## Matching comparison

Both designs use 150 lb multiplied by two downward (300 lbf), up to 300 N
rearward force, up to 100 mm hold projection, all 142 hold positions, and an
additional 25 kg equipment allowance. Each retains its own actual modeled
assembly mass and geometry. The table assigns all rear reaction to one leg,
assumes no sliding, and retains the historical conservative load-angle factors
for both connection columns. Timber is dry, unincised Douglas Fir–Larch No. 2.

| Check; maximum among the indicated sampled cases | 2×6 with original four-bolt detail | 2×8 with six ½-inch bolts |
| --- | ---: | ---: |
| Leg-member interaction, including foot-edge sensitivities | 0.783 | 0.646 |
| Connection lateral ratio, centered foot pressure | 0.990 | 0.403 |
| Connection lateral ratio, both middle-third boundaries | 1.467 | 0.631 |
| Connection lateral ratio, both foot-edge endpoints | 2.751 | 1.304 |

A ratio of 1.0 is the individual analytical reference limit, not physical
collapse. The 2×6 connection uses the conservative thread-root model; actual
bolt grade and shank exposure must be established before using its reference.
The 2×8 connection uses specified smooth-shank geometry. Thus this is a
comparison of complete design approaches, not an experiment isolating lumber
width. The larger design changes both legs and adjoining rims, bolt diameter,
bolt count and layout.

At ideal equal rear-load sharing, the 2×6 connection's middle-third lateral
ratio falls to 0.797, but its foot-edge result remains 1.459. Equal sharing
has not been demonstrated for off-center climbing. The 2×8 exact-angle combined
connection screen reaches 0.644 among its equal-sharing cases. These
sensitivities reinforce that load distribution/contact and the connection
detail determine the decision; neither a centered-pressure assumption nor
equal sharing can be treated as an installed constraint.

The larger candidate still has the previously documented oblique-edge screening
shortfall, unverified prying allowance and bearing-plate material requirement.
The [criterion review](wider-leg-criteria-review.md) explains why the spacing
screen and extreme contact results must not be presented as unequivocal physical
failure predictions.

## Work that would materially increase certainty

1. **Use the published material selection.** The
   [material basis](leg-material-basis.md) specifies Douglas Fir–Larch No. 2 and
   catalog Grade 5 partially threaded bolts. These are design choices already
   made, not unanswered owner questions. For any existing stock, record species/grade,
   dimensions, hole locations, bolt grade, and whether threads or full smooth
   shank bear in each member. In particular, resolve the thread-root assumption
   rather than interpreting it as a measured property of an installed joint.
   Confirm the material properties used for any bearing plates.
2. **Obtain a compatible leg-force calculation.** A timber-connection reviewer
   should determine the joint force/moment and left/right sharing for relevant
   off-center holds, including unilateral foot contact and joint rotation.
   Retain the owner's no-slip assumption; no floor-friction test is requested.
   The calculation must justify joint stiffness/contact assumptions or bound
   their effect. Another arbitrary spring-stiffness trial would not resolve
   this uncertainty.
3. **Resolve the actual connection detail.** Evaluate oblique loaded-edge
   behavior, wood bearing/splitting, bolt combined actions and lap prying using
   those demands. The deliverable should be a specified connection and explicit
   design-load basis, with any required dimensional changes. Single 2×6 stock
   can remain the candidate until that calculation identifies a reason to
   enlarge it. Increasing stock solely because a conservative force assumption
   failed does not establish that the increase is required.
4. **Use a joint-fixture test if the assumed response still controls.** A
   qualified reviewer can specify representative materials, load directions,
   repeated loading and acceptance criteria, then measure joint slip/rotation
   with calibrated loading. This is a bench test of the leg connection, not a
   floor-friction test or a request to use a person as the proof load. One
   successful static loading event would not by itself establish the capacity
   of variable timber joints or repeated use.

These are proposed ways to obtain stronger evidence, not newly completed
qualifications or requirements to reopen panel/T-nut construction. CWA's
[design specification](https://www.cwapro.org/file/secure/cwadesignpecfinal2022.pdf),
sections 4.2 and 8.2, calls for a justified load path and qualified engineering
review. The useful review scope here is the leg assembly and the frame actions
that load it, using the existing drawings and accepted panel design basis.

## Evidence

- [Matched calculation](../fea/leg_150_comparison.py)
- [Results, individual load witnesses and source hashes](../fea/results/leg-150-comparison.json)
- [Three focused tests](../tests/test_leg_150_comparison.py)

The result also records a smooth-⅜-inch-bolt sensitivity on the original 2×6
mass. That entry does not include the historical hardware revision's extra
1.213 kg and is not an approved fabrication-free hardware solution. This
comparison does not change the selected design or adopt a new project weight
rating.
