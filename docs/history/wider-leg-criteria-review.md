# Review of the criteria and their practical limits

The current result combines established wood-design methods with deliberately
conservative load and contact assumptions. They should not have been presented
as equally certain. In particular, the earlier statement that this oblique
connection unequivocally requires 50.8 mm edge distance was too strong.

## Edge distance: a defensible screening choice, not an explicit oblique rule

NDS 2024 Table 12.5.1C specifies 4D for the loaded edge under perpendicular-to-grain
loading and 1.5D for the unloaded edge. At D = 12.7 mm these are 50.8 and
19.05 mm. The current loaded rear edge is 38.045 mm, almost 3D.

The table does not specify intermediate load angles. AWC's earlier commentary
explicitly identifies that gap and the absence of a reduced-edge geometry factor.
The current calculation conservatively applies 4D whenever a bolt has a
cross-grain force component. This is reasonable as an initial screen against
splitting, especially where transverse force is substantial, but its shortfall
does not establish a physical failure or an expressly specified oblique minimum.
Nor does the absence of a rule establish that 3D is adequate. Do not invent a
linear interpolation or borrow the end-distance reduction factor for this edge.
See [the primary-source audit](wider-leg-criteria-sources.md).

The 2018 commentary is used to explain the scope of the table, not to replace
the numerical design values or factors from the 2024 edition.

## Connection resistance: appropriate method, conservative implementation

The dowel calculation uses AWC's yield-limit equations for two wood members
with one shear plane. It includes wood embedment, fastener bending and load
angle. These are design-reference values, already reduced from the modeled
yield mechanism; a ratio above one is not an ultimate break prediction.

The historical implementation uses the maximum angle reduction factor and a
six-fastener group reduction of about 0.951. Both are conservative choices;
the latter is a screening approximation to the actual two/three-fastener rows.
The equal-stiffness elastic distribution of force and moment is also an
assumption, not a measured response of this joint. No bolt-clamping friction
is credited.

Using actual load angles changes the recorded governing lateral ratios only
from 0.817 to about 0.800 and from 1.728 to about 1.683. The governing mechanism
is Mode II, which does not depend on bolt bending yield strength. Raising that
input from the conservative 45 ksi to 92 ksi therefore does not fix those
governing cases. This explains why stronger steel alone is not the answer in
this model.

## Loading: severe project comparison, not a published MoonBoard load rating

The project uses 250 lb at twice body weight downward (2.224 kN), plus 300 N
rearward at up to 100 mm from the face. These are chosen assessment inputs.
The [CWA specification](https://www.cwapro.org/file/secure/cwadesignpecfinal2022.pdf),
Table 1, lists 1.2 kN for an unroped climber and requires applicable material
design and load combinations. Thus our downward input is approximately 1.85
times that published nominal climber load, before the added horizontal force.
This comparison does not establish CWA compliance or imply that all dynamic
climbing forces are bounded by twice body weight.

Assigning all rear load, including dead load, to one leg is a strong asymmetric
scenario. Equal sharing is a useful sensitivity but cannot be assumed for an
off-center climber without a compatible three-dimensional load-path analysis.
The assumed leg-axis reaction direction is another model input: no-slip support
alone does not impose it. These choices deliberately test unfavorable actions
but do not collectively prove an upper bound on every actual joint action.

## Foot pressure: distinguish full contact from a limiting edge case

For a rectangular contact with a linear pressure distribution, keeping the
resultant within the middle third keeps pressure nonnegative over the full
face. Moving farther produces partial contact. This is standard contact
mechanics; see [FHWA's explanation](https://www.fhwa.dot.gov/publications/research/infrastructure/bridge/14094/004.cfm).
It does not mean a flat-cut foot automatically enforces middle-third pressure.

This foot is 190.717 mm long in the fore/aft direction. Its middle-third
resultant range is only ±31.786 mm from the center; its extreme edges are
±95.359 mm. Applying the reaction at an exact edge is a limiting mathematical
case with vanishing contact area, not an established normal operating state.
Near-edge contact can represent substantial rocking or partial contact and
produces a much larger joint moment. It is useful as a robustness sensitivity,
but describing its result as an expected-use failure was too strong.

## Other retained assumptions

The wood calculations use specified dry, unincised Douglas Fir–Larch No. 2,
net sections and stability effects. Normal-duration strength factors are
conservative relative to some legitimately short-duration classifications;
duration must be chosen from cumulative loading and the applicable design
method, not changed solely to obtain a pass.

The 2× prying allowance and assumed 33 ksi bearing-plate yield are still
unverified inputs. A source audit cannot turn them into established properties.
Supplemental EC5 splitting and the conservative linear steel/lateral interaction
are separate analytical checks, not a single unified manufacturer qualification.

## Quantitative limits

The companion [limit sweep](../fea/results/wider-leg-limits.json) recalculates
gravity and fixed horizontal forces at each trial weight. It separates lateral
and combined resistance crossings from the edge-distance screening result.
These are conditional reference crossings, not safe climber ratings. The
geometry deficiency cannot be removed by assigning a smaller climber weight.

Using actual-angle reduction factors, the connection-only combined-reference
crossings with all rear load on one leg are approximately 78 lb at the
board-side foot edge, 323 lb at the board-side middle-third boundary, and
628 lb with pressure centered. Each trial retains twice body weight downward
and the fixed 300 N horizontal load. **These are isolated connection-equation
crossings, not whole-leg limits:** other wood/hardware checks can govern sooner,
and edge geometry/prying remain unqualified. A high centered-pressure number
must not be used as a user-weight rating.

Rechecking all existing numerical wood/hardware metrics at each trial gives
the following earlier governing crossings. These retain actual-angle lateral
factors and normal-duration wood references:

| Pressure resultant, all rear load on one leg | First numerical crossing | Governing check |
| --- | ---: | --- |
| Board-side foot edge | 78.2 lb | Conservative bolt lateral plus axial |
| Board-side middle-third boundary | 323.3 lb | Conservative bolt lateral plus axial |
| Center of foot | 350.0 lb | Bearing-plate plastic bending |

These are **conditional design-reference crossings, not approved climber
weights or physical breaking weights**. The plate-controlled value specifically
depends on the assumed plate yield strength and prying amplification. All three
precede the computed loss of front compressive contact. At the middle-third
crossing the plate and leg-member ratios are approximately 0.967 and 0.907;
at the centered crossing they are 1.000 and 0.838. The 628 lb connection-only
number is therefore not the governing numerical limit at centered pressure.
The weight sweep varies the climbing cases. Independent review separately
checked permanent-only cases with CD = 0.9 and kmod = 0.6 at these same three
pressure positions; their peak ratios were 0.587, 0.264 and 0.252, respectively.
They do not govern the listed crossings. Independent ±5% weight checks also
bracketed unity at all three reported crossings.

The calculation also identifies the first loss of compressive front contact,
using the total rear reaction before dividing it between legs. It flags weight
crossings outside that domain; no assumed tensile floor reaction is accepted.
This is a contact-model consistency check, not floor-friction qualification.

At the original conservative angle factors and 250 lb doubled-load input,
with all rear load assigned to one leg, the combined lateral/axial reference is
satisfied only while the pressure resultant lies approximately **42.55 mm
toward the board to 44.50 mm away from the board**, measured from the foot
center. This interval is wider than the middle third (±31.79 mm), but much
narrower than the full foot (±95.36 mm). Ideal equal sharing satisfies that
connection reference across the full foot in the same model.

The reference crossing therefore does not require the impossible ideal of
finite force on a zero-area edge. Under an assumed triangular partial-contact
pressure distribution, those crossing positions correspond to roughly 80–83%
of the foot remaining in contact. That is a mechanics interpretation of the
computed resultant, not a prediction that this assembly actually lifts or rocks
to that state. It is a reason to retain contact sensitivity while avoiding the
claim that the extreme-edge result predicts normal behavior.

![Conditional pressure and sharing sensitivity](wider-leg-review/pressure-sensitivity.png)

The graph retains the original conservative angle factors so it can be compared
directly with the preceding assessment. The result file separately records the
actual-angle and short-duration sensitivities. Reproduce with
`uv run python -m fea.wider_leg_limits` followed by
`uv run python -m fea.plot_wider_leg_limits`. Five focused tests cover load
affinity, baseline parity, bracketed crossings, unilateral contact and the
all-metric wood/hardware comparison.
