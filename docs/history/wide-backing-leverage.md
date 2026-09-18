# Lower-backing retention leverage

This is an exact **conditional planar statics calculation**, not a new FEA
solution or measured bolt demand. It uses the current `wide-principal-development`
attachment coordinates. No part or connection has been redesigned.

## Question and assumptions

The continuous lower backing is retained at the two principals by bolts at
X = −82.55 and +44.45 mm, only 127 mm apart. Six panel attachments enter this
backing, including four well outside those support axes. What reactions would
an isolated outward load require if two point supports at those axes were the
only restraint in the board-normal direction?

The model projects each attachment to the bolts' common S = 40 mm station,
allows both signs of support reaction and assumes no applied support moment.
It does not model rail stiffness, finite housing contact patches, panel load
sharing, rim-end attachment, bolt compliance, preload or strength. It is neither
a conservative bound nor a replacement for the complete physical joint.

For outward load P at X = x, positive support reaction acts inward (+N):

`R_left = P × (x_right − x) / (x_right − x_left)`

`R_right = P × (x − x_left) / (x_right − x_left)`

These satisfy normal-force balance and moment balance about the S axis. Positive
reaction requires an inward retention path; negative reaction requires outward
compression/contact. A bolt is not assigned a negative tensile force.

## Current attachment influence coefficients

| Panel attachment suffix | X (mm) | R_left / P | R_right / P |
| --- | ---: | ---: | ---: |
| lower_left_3 | −82.55 | 1.000 | 0.000 |
| lower_left_9 | −791.15 | 6.580 | −5.580 |
| lower_left_10 | −448.15 | 3.879 | −2.879 |
| lower_right_1 | 44.45 | 0.000 | 1.000 |
| lower_right_9 | 412.75 | −2.900 | 3.900 |
| lower_right_10 | 809.45 | −6.024 | 7.024 |

Thus an illustrative **100 N outward force at the rightmost attachment** needs
702.36 N inward reaction at the right support and 602.36 N outward reaction at
the left in this model. This is not a prediction that a climber applies 100 N
there, or that the right bolt actually carries 702.36 N. The finite housing and
connected panels can change the load path materially.

The real attachment stations are S = 19.05 or 60 mm, not 40 mm. Their omitted
load moments about world X are respectively +20.95 or −20 Nmm per newton of
outward force. The [machine-readable result](../fea/results/wide-backing-leverage.json)
retains these moments explicitly. Two normal point reactions at a common S
cannot balance that torsion alone. A complete model needs additional contact
and/or rotational load paths; these numbers are not a full six-component joint
solution.

## Design consequence

The subsequent [relaxed housing-contact bound](wide-backing-contact-bound.md)
includes the real attachment S offsets and full housing envelopes. Its optimistic
minimum total retention remains up to 5.462 N/N within that isolated normal-only
model. It does not establish actual bolt demand or whole-frame performance.

Do not assess the backing by allocating half a panel or board load to each bolt.
Widening the principals corrects an edge-distance screen but does not, by itself,
remove the backing's long overhangs or prove adequate retention. The next useful
comparison is the existing central retention with its finite housing contacts
versus additional distributed retention nearer the outer attachments. Check
panel/LED access and disassembly before selecting any new end connection.

The [wood-bearing envelope](backing-bearing-envelope.md) remains a single-mode
conditional resistance, not an allowable for this joint. Do not compare a
climber's weight directly to it using these coefficients: the actual force P,
load combinations, torsional restraint and other failure modes are unresolved.
This calculation establishes a reason to investigate the load path, not a
failure verdict or a heavier-stock recommendation.

Reproduce with `uv run python -m fea.wide_backing_leverage` and
`uv run pytest -q tests/test_wide_backing_leverage.py`. Nine tests cover signed
force/moment balance, invalid inputs and current six-attachment replay. The
generator authenticates the existing export source/inventory before evaluating
the current CAD connection positions. Historical evidence is unchanged.
