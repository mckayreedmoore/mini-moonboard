# Leg stock comparison — geometry and rigid-floor screens

The current paired-plywood legs cannot simply be replaced with narrower straight
lumber while retaining their bend and bolt pattern. This comparison identifies
geometry, section and rigid-floor tradeoffs before candidate-specific elastic
frame solves. **No new leg is selected or approved for construction yet.**

## Current leg and proposed directions

Each current leg comprises two nominal 19.05 mm plywood plies, with a 180 mm
wide continuous bent profile. Four rim bolts occupy stations spanning 280 mm.
The lower centreline meets the level floor at Y = 1403.998 mm and is about
20.891 degrees from vertical. The two plies have separate physical identities;
the existing coupled-frame trial nevertheless bonds them together internally.

A straight board aimed from that floor centre through the four-bolt centroid
is about 14.716 degrees from vertical. It needs **239.676 mm of width just to
contain the complete existing bores**, before qualifying connection edge/end
distances or washer placement. Actual 2×10 width is only 234.95 mm. A 2×12
contains the bores geometrically but leaves only 28.593 mm minimum hole-centre
distance to a side edge (23.037 mm clear bore ligament). Its wider level foot
changes the contact footprint. Geometric containment is not a fastening rating.

Two useful candidate directions follow:

- A re-aimed straight leg with a revised, checked attachment layout. Investigate
  the 2×12 direct layout, but do not treat the old holes as automatically usable.
- A straight lower member plus detachable plywood knee/cheek adapters. This
  retains a possible route for all four stock sizes without cutting solid lumber
  into a cross-grain hockey-stick shape. The additional joint, eccentricity and
  bolt stack need explicit design and testing.

The second route makes 2×8 a useful **starting candidate**, not a strength-based
selection: its 184.15 mm width is close to the current 180 mm lower member.

## Gross-section comparison

Dry dressed dimensions follow [ALSC PS 20-25, Table 3](https://alsc.org/uploaded/PS%2020-25%20Final.pdf),
using exact conversion of the inch dimensions. All lumber options are 38.1 mm
(1½ in) thick. Ratios below compare equal modulus and equal length with an
ideal fully bonded 38.1 × 180 mm plywood strip. They are section properties,
not allowable loads or actual whole-board displacements.

| Stock | Width, mm / in | Sideways bending stiffness ratio | In-plane bending stiffness ratio |
| --- | ---: | ---: | ---: |
| Plywood, bonded reference | 180 / 7.087 | 1.000 | 1.000 |
| Plywood, independent equal-share plies | 180 / 7.087 | 0.250 | 1.000 |
| 2×6 | 139.7 / 5½ | 0.776 | 0.468 |
| 2×8 | 184.15 / 7¼ | 1.023 | 1.071 |
| 2×10 | 234.95 / 9¼ | 1.305 | 2.224 |
| 2×12 | 285.75 / 11¼ | 1.588 | 4.001 |

Depth helps in-plane bending much more than sideways bending. Increasing width
alone does not solve lateral restraint or joint slip. The separate
[actual bent-leg fixed-bore test](../fea/results/independent_leg_response/README.md)
found about 3.922× sideways compliance for independent equally loaded plies
versus its bonded reference; that actual-shape result is distinct from this
straight-strip factor of four.

The executable screen also evaluates floor-centre extensions of 150 and 300 mm
beyond the current location, retaining the bend datum for the strip-length
comparison. That length rises from 1517.706 to 1648.683 mm at +300 mm. At equal
section/modulus, cantilever compliance increases with length cubed and ideal
Euler load decreases with length squared. A longer footprint therefore has a
member-flexibility cost; its stability benefit must be checked with the changed
mass, centre of gravity and contact polygon. The direct straight attachment
calculation separately re-aims each stock through the existing bolt centroid;
its length is **not** the bend-to-floor surrogate length.

## Reproduce and interpret

```sh
uv run python -m fea.leg_stock_screen
uv run pytest -q tests/test_leg_stock_screen.py
```

The report contains gross area, both second moments and section moduli,
equal-E unit cantilever compliance, separate ideal K=1 Euler references, and
side-edge bore-fit results. E = 7000 MPa is deliberately the same numerical
comparison value for every stock, **not** a selected material property. The
Euler references are not NDS column resistances, and K=1 is not inferred from
the cantilever fixture. No climber rating follows from either calculation.

## Straight-leg CAD comparison

`mini_moonboard.lumber_leg_frame` now defines all four stock sizes with 0, 150
and 300 mm additional foot-centre extension. These are **new-build alternatives**,
not instructions to reuse or plug previously drilled rim holes. The existing
default design remains unchanged. All twelve alternatives are selectable in the
[interactive viewer](https://mckayreedmoore.github.io/mini-moonboard/?model=lumber-leg-2x8-e150).
Each displays the actual complete candidate assembly, including new leg/rim
bores and bolts, with metric and imperial dimensions. These are unqualified
comparison views, not a selected replacement or a retrofit drilling guide.

Each leg is one straight 38.1 mm thick member: grain along its length, a square
top cut and a horizontal full-width floor cut. All variants fit a nominal 8 ft
length geometrically, before allowing for stock end trimming and kerf. The new
bolt group is centred at board station S=1680 mm and rim depth N=92.075 mm.
Its four corners form a parallelogram with 50 mm side vectors along the leg
grain and rim grain. Both members therefore have two grain-parallel rows.
The upper cut is 120 mm along the leg beyond the group centre.

The nominal spacing screen checks 50 mm in-row pitch, transverse row spacing
against 35.719 mm at member thickness/bolt diameter = 4, loaded side edges
against 4D and the leg top against 7D. These comparisons use
[NDS 2024 Tables 12.5.1A–D](https://awc.org/wp-content/uploads/2026/08/AWC_NDS2024_withCommentary_20250328_WebsiteChapter-12-%E2%80%93-Dowel-type-fasteners.pdf).
They do not establish adjusted resistance, splitting resistance or installation
tolerances. In particular, the compact pattern changes the bolt moment arms;
the old four-bolt force results must not be transferred to it.

The provisional joint has two 38.1 mm members and retains the existing nominal
3/8-16 × 3¾ in bolt family, with 11.1125 mm clearance bores. Plywood stitch bolts
are removed. Each assembly has 101 bodies and 182 connection assemblies; all
non-leg/non-rim bodies and non-leg fasteners retain their current geometry.
Rims are rebuilt before drilling so obsolete leg bores do not remain.

```sh
uv run pytest -q tests/test_lumber_leg_frame.py
uv run python -m fea.lumber_leg_floor 2x8 --extension 150 --output /tmp/leg-2x8-e150.json.gz
```

CAD checks cover all twelve leg shapes and level feet. Full new-bolt/wood and
new-bolt/other-hardware collision checks cover all twelve variants. These checks
are not physical joint tests.
The floor command recalculates drilled mass, CG and contact hull, then reuses
the established 1296-case unanchored rigid-floor screen at assumed friction
coefficients 0.1, 0.2 and 0.4. It refuses to overwrite an existing report.

### Rigid-floor comparison results

All thirteen models (current plywood plus twelve lumber/extension variants)
have admissible compression-only equilibrium witnesses for all 1296 cases at
assumed μ=0.2 and μ=0.4. No variant covers every case at μ=0.1. Counts below are
feasible cases out of 1296 at that lower assumed friction, not safety factors:

| Stock | Current foot centre | +150 mm | +300 mm |
| --- | ---: | ---: | ---: |
| Existing plywood | 683 | Not changed | Not changed |
| 2×6 | 664 | 673 | 678 |
| 2×8 | 678 | 685 | 696 |
| 2×10 | 702 | 715 | 716 |
| 2×12 | 714 | 721 | 736 |

The [saved reports](../fea/results/lumber-leg-floor/) include actual model mass,
CG, contact hull, source fingerprints, full cases and equilibrium witnesses.
All wood uses the same assumed density of 600 kg/m³, with 80/100% included-mass
sensitivity; this is not a measured stock-density comparison. Bolt, insert,
hold and LED mass remain excluded. Each wider/longer leg changes both included
mass and contact geometry, so the table does not isolate footprint alone.

These finite rigid-body results do not justify choosing the widest or longest
leg. They also do not establish actual friction, compliant floor contact, joint
force distribution or structural adequacy. Infeasibility of the inscribed
polygonal friction approximation is not proof that a circular friction cone
is infeasible. The unresolved member/joint comparison still controls selection.

```sh
uv run pytest -q tests/test_lumber_leg_floor.py
```

Verification: the combined stock, CAD and saved-floor replay suite passed
51 tests. Independent correctness, testing and package reviews found no
substantial remaining issues in this stage after a missing contact-hull source
fingerprint was added and every floor case rerun. This review is not structural
approval and does not close the remaining tasks below.

The [coupled-frame comparison](lumber-leg-response.md) now documents the independent
leg meshes, revised connector points and accepted native results for all four
stock sizes at zero extension, plus 2×8 at +300 mm.
The selectable viewer variants are available. Neither result ranks leg strength.

Conditional section and direction-dependent single-bolt references are included.
A two-resolution leg-mesh check did not reverse the joint-development concern.
The working development preference is 2×8/+300 mm with a revised bolt group;
combined member/connection qualification remains open.
No strength-based leg selection has been made. External material, connection
and final installation verification remain open.
