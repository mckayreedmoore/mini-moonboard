# Taper method applicability review

## Current disposition

The original six-case taper checker passes its implemented equations, but this
review identified additional justification needed before completion. Preserve
those calculations as evidence; do not equate their count with a complete local
stress assessment.

The [USDA Wood Handbook, Chapter 9](https://research.fs.usda.gov/download/treesearch/37423.pdf),
pp. 9-4–9-5, distinguishes uniform-beam shear from tapered-beam stresses. The
sloping face can have longitudinal shear and transverse normal stress induced
by bending. Its example is a particular uniaxially loaded tapered beam; applying
that example directly to a biaxially loaded leg with axial force is insufficient.
The handbook also gives rectangular torsion equations for wood on p. 9-7. This
supports a handbook-level rectangular comparison, but not unresolved taper,
bore or load-introduction stresses.

## Required checks

1. Map actual grain, taper-thickness direction, support reactions and joint
   forces to each source equation. The 139.7 mm dimension is constant; the
   transverse 88.9 mm thickness tapers to 50.8 mm.
2. Derive or otherwise establish the tapered-face shear/transverse-stress
   contribution under actual axial and biaxial section resultants. The existing
   uniform-rectangle shear formula alone does not establish that contribution.
3. Explain the support-notch comparison's field of applicability. Its computed
   reduction factor is 1.0 in all six old cases, so the mixed EC5/ASD calculation
   must not be called a demonstrated conservative bound without that explanation.
4. Check the relevant stress combination with a supported material/resistance
   basis; do not invent perpendicular-grain tension capacity or use clear-wood
   averages as grade design values.
5. Keep local bolt-hole and support-region comparisons distinct from unbored
   section equations, and use the new contact-enabled forces for the flush
   revision when numerical acceptance is established.

These are bounded analytical checks, not a new floor test, panel campaign,
external-review requirement or instruction to change the selected lumber.

## September 14 disposition: applicability gate remains open

The cited EC5 calculation is an end-notch fracture comparison, not a complete
combined-load taper calculation. [Swedish Wood, Glulam Handbook Volume 2](https://www.swedishwood.com/siteassets/5-publikationer/pdfer/glulamhandbook2-240508.pdf),
pp. 70–71, relates its reduction factor to support shear and the support load
line. Its inclined-notch modification incorporates experimental evidence.
The same source separately requires a tapered-edge bending-strength reduction
on pp. 103 and 107 to account for simultaneous shear and transverse normal
stress. The tensile-edge version needs perpendicular-grain tensile resistance;
the compressive-edge version needs perpendicular-grain compressive resistance.
The document covers glulam design, and its equations are not themselves a
qualification of the project's sawn DF-L ASD material basis.

The current implementation uses `h = 88.9`, `hef = 50.8`, `b = 139.7` mm and
`i = 12`. Rotating the section axes maps the geometric side-width reduction to
that notation, but does not map all the actions: the leg also carries axial
force, bending about both transverse axes, torsion and a distributed floor/joint
load path. Computing `kv = 1` therefore does not demonstrate that the omitted
taper-edge interaction is bounded. Calling the US/EC5 hybrid "intentionally
conservative" is unsupported until that mapping and resistance basis exist.

### Current-force diagnostic, not a resistance pass

A direct plane-section diagnostic of the first accepted contact-enabled flush
case provides a concrete reason not to select only the compression-side taper
formula. Input:

- `fea/generated/floor-flush-first/a12-left/block-01/report.json`
- SHA-256: `91831a6abf62ecee7a14795e5100a2587daaa77cfe2709c8b1a9e6ab5c2224ee`
- Upper-load free-body conventions from `fea/reinforced_frame_demand.py`:
  `u = +X`, `v = normal_axis_xyz`, `u × v = grain`.

For each unbored retained rectangle, let `w` be its remaining X thickness,
`d = 139.7`, `c = outward_sign * removed_thickness / 2`, and let signed `N`,
`Mu`, and `Mv` be the recorded section actions. Translate the moment to the
retained centroid: `Mv_c = Mv + c*N`. At the two corners on the cut face,
`u = -outward_sign*w/2` and `v = ±d/2`, ordinary plane-section stress is:

```text
sigma_grain = N/(w*d) - Mv_c*u/(d*w^3/12) + Mu*v/(w*d^3/12)
```

At taper-start station −211.8535446 mm, the left leg's two corner stresses are
−0.559485 and **+0.021506 MPa**, respectively. The right leg's corresponding
range is −0.625776 to −0.235861 MPa. These are nominal longitudinal stresses,
not recovered three-dimensional local stresses or a perpendicular-grain
strength check. Positive tension at one corner means axial compression alone
cannot justify classifying the entire tapered face as compression-only. Interpolating the constant axial force
and affine moments just 1 mm inside the taper gives +0.020239 MPa at the same
corner, so this diagnostic is not confined to the slope-transition endpoint.

For a smooth, traction-free sloping face described by `u(s)`, boundary traction
equilibrium implies `tau_su = u'(s)*sigma_ss` and
`sigma_uu = u'(s)^2*sigma_ss`. Thus a tensile longitudinal face stress also
implies a tensile transverse component in that idealization. This mechanics
identity supplies no allowable resistance and no local-transition stress bound.
The nominal left-corner value would imply approximately 0.000149 MPa transverse
tension at a 1:12 slope; its small magnitude is **not** permission to assign
positive allowable tension perpendicular to grain.

The report contains both taper boundary stations, but no strictly interior
taper recovery station. In the present connector-load model there are no force
jumps between them, so section forces are constant and moments affine there.
Interior extrema of stress divided by changing section properties cannot be
assumed to lie at these endpoints. The supplementary analytic diagnostic below
now closes this sampling question for nominal longitudinal stress in this case;
it does not close local tapered stress or resistance applicability.

### Supported paths to a closed decision

1. **Retain this taper:** establish a material-compatible local stress/fracture
   method covering its combined actions, both taper transitions and any tensile
   edge contribution; bound stress extrema throughout the taper; then apply it
   to every accepted current case and fabrication limit. This is unresolved,
   rather than an instruction to import clear-wood average tensile strengths or
   mix EC5 characteristic strengths into the ASD schedule.
2. **Remove the local recess:** put each runner alongside an uncut rear leg,
   keeping the runner itself outboard of the kicker. This eliminates this
   particular side-width taper gate. It requires a new front runner/post
   connection alignment, bolt lengths/spacing, overall-width review and fresh
   current solves; no existing pass transfers. It is a concrete alternative to
   study, not an already selected or checked detail.
3. **Reinforce the local detail:** a catalog reinforcement designed for the
   entire relevant transverse force could avoid relying on timber transverse
   tension, but needs a supported load derivation, installation geometry and
   product resistance basis. No such reinforcement is currently specified.

None of these paths adds a floor test, independent panel assessment or external
sign-off gate. The present decision is **not construction-qualified by the
implemented taper equations**; it is not a demonstrated physical failure.


### Completed nominal-extrema diagnostic

[`scripts/flush_taper_stress_diagnostic.py`](../scripts/flush_taper_stress_diagnostic.py)
computes exact corner extrema of the nominal plane-section model between every
recorded force jump. For normalized station `t`, remaining width is affine and
corner stress is `p(t)/w(t)^2`, with quadratic `p`. The numerator of its derivative,
`p'(t)*w(t) - 2*p(t)*w'(t)`, is affine. Endpoints and its possible interior root
therefore enumerate the extrema. The script validates the constant axial/shear
forces and moment gradients against free-body equilibrium before applying this
calculation. No new native solve or interpolation of local finite-element stress
is involved.

[Machine-readable result](flush-taper-stress-diagnostic.json) preserves the input
report SHA-256 and all extremum candidates. For A12-left, maximum nominal
cut-face longitudinal stress is +0.021506 MPa on the left leg and −0.054666 MPa
on the right. These maxima happen to lie at boundary stations; that result is
now calculated, not assumed. Three focused tests verify a known interior peak,
the right-handed signed-moment convention, and agreement with independently
evaluated dense corner stresses. The local taper applicability and resistance
gate remains open.

Reproduce from repository root:

```sh
uv run python -m scripts.flush_taper_stress_diagnostic \
  fea/generated/floor-flush-first/a12-left/block-01/report.json \
  docs/flush-taper-stress-diagnostic.json
uv run pytest -q tests/test_flush_taper_stress_diagnostic.py
```
