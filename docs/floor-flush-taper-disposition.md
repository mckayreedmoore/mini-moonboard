# Rear-leg taper disposition and geometry alternatives

Assessment date: September 14, 2026. Current authority remains
`compact-floor-flush-development`; this review selects no replacement and
changes no drilling or resistance threshold.

## Decision

The available evidence does **not establish a positive local resistance
decision for the current rear-leg taper under the adopted sawn DF-L No. 2 ASD
basis**. It also does not demonstrate physical failure. The actionable next
choice is between a supported reinforced/local-detail method and a separately
modeled uncut-leg arrangement. Merely running the remaining global cases or
lengthening the taper cannot close the present material/method gap.

The existing [taper review](taper-method-applicability-review.md) and exact
[nominal-extrema diagnostic](flush-taper-stress-diagnostic.json) remain valid
evidence. Their A12-left maximum cut-face longitudinal tension is
0.021506 MPa. The ideal smooth-face traction relation at a 1:12 slope implies
about 0.000149 MPa transverse tension at that nominal point. Neither number is
a recovered local fracture stress or a resistance comparison. The two taper
transitions, holes and load-introduction regions remain separate local issues.

## What the primary methods permit

[NDS 2024 Chapter 3](https://web-media.awc.org/wp-content/uploads/2021/12/17210019/AWC_NDS2024_withCommentary_20240718_AWCWebsite_Chapter-3-Design-Provisions-and-Equations.pdf),
§3.7.2, supplies a representative dimension for tapered-column compression and
stability checks. It does not supply a transverse-tension allowable or a
combined local taper-fracture criterion. Section 3.8.2 directs avoiding
perpendicular-grain tension where possible and considering mechanical
reinforcement sufficient to resist it when unavoidable. This review checked
the previously downloaded AWC chapter at `/tmp/reinforced-NDS2024-ch3.pdf`
and its extracted text; the live chapter URL did not reopen successfully.

[AWC's NDS 2018 commentary](https://awc.org/wp-content/uploads/2021/10/AWC_NDS2018-withCommentary_20200827_AWCWebsite_Commentary.pdf),
C3.8.2, explains why sawn-lumber perpendicular-tension design values are not
published: commercial lumber can contain checks, shakes and drying splits
that make clear-specimen strengths inappropriate. This is explanatory
background, not permission to mix editions or assign one third of the
parallel-shear allowable to this grade.

[USDA Wood Handbook, Chapter 9](https://research.fs.usda.gov/download/treesearch/37423.pdf),
pp. 9-4–9-5, identifies transverse normal and shear stresses at a sloped beam
face. Its illustrated bending solution does not itself furnish the present
sawn-grade resistance or cover all the axial, biaxial, torsional and local
connection effects.

Consequently:

- A small calculated transverse tension cannot be divided by an invented
  positive allowable, ignored by rounding, or classified as compression.
- The existing EC5 support-notch factor of 1.0 is not a demonstrated bound
  for this distinct combined-load problem. Glulam tapered-edge resistance
  equations cannot automatically qualify the present sawn-lumber ASD basis.
- A refined elastic solid model alone would improve demand recovery, but
  would still need a compatible resistance/fracture basis and treatment of
  cut transitions and defects. A numerical corner peak is not that basis.
- Ordinary bolt or panel-screw checks do not establish mechanical
  reinforcement against this transverse-tension mechanism.

## Exact translation alternatives

The actual left-side transverse bounds reconstructed from
[`floor-flush-geometry.json`](floor-flush-geometry.json) are below. Right-side
bounds mirror about X = 0. Dimensions are millimetres.

| Member | Minimum X | Maximum X |
| --- | ---: | ---: |
| Full uncut rear leg | −1308.1 | −1219.2 |
| Current runner | −1257.3 | −1219.2 |
| Current front outer post | −1219.2 | −1181.1 |
| Current side rim | −1219.2 | −1130.3 |

These are transverse bands, not an assertion that all listed members occupy
the same Y/Z volume. Current runner overlaps the first 38.1 mm of full leg
thickness in X; the recess resolves their actual rear intersection.

| Separate geometric study | Minimum translation | Immediate consequence |
| --- | ---: | --- |
| Move runner inward alongside uncut leg | 38.1 per side | Runner band becomes the current front-post band; post intersection and kicker clearance must be resolved. |
| Move runner fully outside uncut leg | 88.9 outward per side | Runner inner face reaches the full leg outer face; front runner/post connection gains an 88.9 gap. |
| Keep runner; move uncut leg outward | 38.1 per side | Rear runner/leg interface fits; upper leg/rim interface gains a 38.1 gap. |

The inward-runner approach already has a preserved precedent:
`compact_floor_rail_frame.py` moved front posts inward by 38.1 mm and cut
40.1 mm-wide kicker edge clearances. That detail conflicts with the current
whole-kicker preference and is not the default remedy.

The fully outboard runner increases timber envelope width by 38.1 mm on each
side relative to the existing leg outer faces; its **runner translation** is
88.9 mm. These are different measurements. Its nominal rear two-member wood
grip becomes 127.0 mm (88.9 leg + 38.1 runner), replacing 88.9 mm. Moving the
uncut leg instead increases each outer leg extent by 38.1 mm and has the same
rear grip, but disrupts the upper joint.

No single translation preserves all existing two-member joints and the whole
kickers. A bolt spanning either new gap is not the current bearing/yield
model. A spacer, wider receiver or connector would be a new explicitly checked
connection; none is selected here. Widening or moving front posts also needs
actual kicker screw-receiver and bracket checks. Do not assume built-up or
composite vertical stock to fill these gaps.

## Finite next work

For a retained taper, first establish the local method and material-compatible
resistance basis, including mechanical reinforcement if used. Bound demand
over the complete runout and both transitions under every accepted current
case and fabrication limits. Only then can a finite pass/fail ratio be stated.

For an uncut-leg study, first draw one complete front-to-rear connection
arrangement, including the upper joint, without gaps being silently treated as
wood bearing. Preserve the whole kickers, outward bolt tips, floor-supported
timber and requested end planes where feasible. Then update actual contact,
eccentricities, stock, grip and thread/runout geometry, bolt placement,
member/connection resistance and all current-case forces. Existing passes do
not transfer. This removes the specific side-thickness taper gate; it does not
automatically resolve the separate flush rim cut or angle moment demands.

No new floor test, panel qualification campaign, external-review gate,
larger-base selection or construction release follows from this disposition.
