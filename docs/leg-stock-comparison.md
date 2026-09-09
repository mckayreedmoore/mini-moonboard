# Leg stock comparison — initial geometry screen

The current paired-plywood legs cannot simply be replaced with narrower straight
lumber while retaining their bend and bolt pattern. This first comparison
identifies the geometry and section tradeoffs before candidate-specific frame
solves. **No new leg is selected or approved for construction yet.**

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

Next deliverables are actual leg/adapter CAD variants, checked joint geometry,
candidate-specific coupled-frame response and floor-equilibrium comparisons,
and source-supported member/connection resistance checks. Retain the current
viewer and cut list until the replacement geometry and hardware are consistent.
External material, connection and final installation verification remain open.
