# Current bracket orientation audit

This audit covers only `wide-principal-development`: eighteen ML24Z angles and
108 SDS25112 screws. It does not qualify a connection or assign individual
bracket forces. The older [ML24Z reference](ml24z-qualification.md) describes a
different, twenty-angle bearing-frame candidate; its installation mapping must
not be applied to this one.

## Established geometry

The [generated per-bracket schedule](wide-bracket-axes.csv) identifies both wood
members, all six screws, the virtual bracket corner in millimeters and inches,
and three right-handed unit axes in world coordinates. The source is the same
`wide_frame.stations()` used by the actual CAD. Generation first authenticates
the current export's source hashes and hardware inventories.

| Current locations | Count | Bend-line axis, ignoring sign | Intended member grain |
| --- | ---: | --- | --- |
| Top rail, both ends of each half | 4 | Board normal N | Rail X; rim/principal S |
| Two middle rails, both ends of each half | 8 | Board normal N | Rail X; rim/principal S |
| Header to two outer and four center posts | 6 | World Y | Header X; posts world Z |

X is board width; S is uphill along the inclined board. Here
`S = (0, 0.642788, 0.766044)` and `N = (0, -0.766044, 0.642788)`.
World Z is upward. World Y is horizontal, not the inclined board normal.
Individual signs differ between mirrored placements; use the CSV rather than
assigning one signed vector to every bracket.

In each row, U lies along the first flange into its open quadrant; V lies along
the second flange; W = U × V follows the bend. Beam screws enter along −V and
upright screws along −U. Three screws must be assigned to each named member.
For a force expressed in world coordinates, its geometric components are
`(F·U, F·V, F·W)`. These are **not automatically the manufacturer's F2/F3/F4
components**. Specify which member's action is being reported and the applicable
installation figure before assigning those names or signs. A moment also needs
to be transferred to the stated reference point before changing axes.

## What the manufacturer evidence establishes

The [L-C-MLZ25 letter](https://ssttoolbox.widen.net/content/iczmiabsx6/pdf/L-C-MLZ25.pdf)
was downloaded again on September 8, 2026; its SHA256 matches the existing
[reference record](ml24z-reference.json):
`88d9051a9eadc08508a1a1c591914217309d6a2c1a281b375149d0cc57e584ff`.
Both its text and installation figures were inspected. F1 follows the bend
line. The other labels depend on the installed member arrangement; the bearing
table does not list F2. No installation classification or mixed-direction
resistance is selected by this geometric audit.

The assumed bend axis is perpendicular to both members' grain at all eighteen
positions. This makes the letter's cross-grain bending/tension consideration
relevant to any subsequently recovered F1 action. It does **not** prove tensile
stress, splitting, inadequate capacity or that reinforcement is required at
every bracket. Those decisions require the actual joint force and local load
path. Likewise, screw axes are perpendicular to intended grain throughout this
schedule, but this alone does not establish edge distance or screw resistance.
Actual stock grain and installation still require inspection.

## Next connection check

Recover forces across a defined joint interface, excluding unrelated bonded
paths. Identify the loaded member, transfer its wrench to the bracket group,
and map it to the appropriate manufacturer figure. Do not equally divide a rail
or frame resultant among its angles. Where installation or combined-load
treatment remains unlisted, send this placement schedule and calculated demands
to the manufacturer or structural reviewer. No inquiry has been sent.

Reproduce with:

```sh
uv run python -m scripts.wide_bracket_axes
uv run pytest -q tests/test_wide_bracket_axes.py
```

The tests check all eighteen placements and 108 unique screws, both orientation
families, orthonormal handedness, reversible force projection, metric/imperial
origins, explicit grain assumptions and exact published CSV replay. They do not
test connection strength.
