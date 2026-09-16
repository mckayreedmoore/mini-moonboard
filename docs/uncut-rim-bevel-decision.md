# Uncut full-rim bevel resistance decision

Date: September 14, 2026.

## Decision

**Reject the reviewed resistance route.** No cited primary method supplies a
material-compatible qualification for the full horizontal bevel in conventional
solid-sawn Douglas Fir–Larch No. 2 under the accepted A12-left angled bearing
and combined section actions. This is a supported method rejection, not a
prediction that the rim physically fails.

The conditional NDS compression-taper mapping cannot cover both rims because
the right rim's shortened q+ face is in nominal longitudinal tension at the
first adjacent full section. The tension is small but nonzero and is not
discarded. The NDS tension-face route does not define an equivalent remaining
depth for this zero-tip full bevel bearing directly on its sloping end, and its
end-notch shear expression is not a complete local combined-action or fracture
method. No allowable or stress-concentration factor is introduced.

`compact-floor-uncut-development` remains unselected and is not advanced to
contact refinement or the other five global cases by this result.

## Accepted demand and face mapping

Source is the accepted no-slip A12-left archive at
`fea/results/floor-uncut-first/a12-left`. The uncompressed native report has
SHA-256
`d1d8b6e4747a6f2875b1811fcf0fc7001c55dba82677b33305b08b81bcafcc81`.
It converged in 11 contact cycles and passed its equilibrium, MPC and normal-
contact checks. Its provisional connection representation and separate open
connection gates do not affect this bounded method disposition.

Both rims have an 88.9 by 139.7 mm full section. The report uses
`section_u = -X` and `section_v = (0, -cos(40 degrees), sin(40 degrees))`.
The bevel shortens the opposite depth face, so q+ is `v = -d/2`. At the first
recovered full section, station 58.611109 mm, the nominal longitudinal corner
stress is reproduced directly from the archived section resultants as

```text
sigma = N/(b d) - Mv*u/(d b^3/12) + Mu*v/(b d^3/12)
```

with `u = +/-b/2`, `v = -d/2`, and tension positive.

| Rim and station-load convention | N (N) | Vu (N) | Vv (N) | Mu (N mm) | Mv (N mm) | T (N mm) | q+ corner range (MPa) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Left, exclude coincident station loads | -47.522918 | 14.817816 | 459.028637 | 38,236.524218 | -717.075416 | -19,092.499545 | -0.139955 to -0.132161 |
| Left, include coincident station loads | 138.472672 | 14.817816 | 615.097469 | 25,244.732201 | 7,550.428594 | -26,029.759111 | -0.117185 to -0.035121 |
| Right, exclude coincident station loads | -21.629677 | 10.645907 | -44.283040 | -3,257.167398 | -1,481.442890 | -4,082.912392 | +0.001472 to **+0.017573** |
| Right, include coincident station loads | -21.629677 | 10.645907 | -44.283040 | -3,257.167398 | -1,481.442890 | -4,082.912392 | +0.001472 to **+0.017573** |

Thus the left adjacent q+ face is compression in both conventions, while the
right adjacent q+ face is tension and reaches 0.017573 MPa. These are gross,
plane-section values adjacent to the bevel. They do not recover the local
bevel-edge or full-to-taper transition stress and are not used to infer one.
Their bounded use is to reject a blanket compression-only classification.

The horizontal bevel itself runs from Y = -223.862730 to -41.497331 mm at
Z = 277 mm. Remaining grain-normal depth grows from zero at the exterior tip,
through 36.894791 mm at the outer header edge, to the full 139.7 mm at the
inner header edge. Actual header bearing is 134.202669 mm long; the exterior
free tail is 48.162730 mm. The end is 40 degrees from a grain-normal square cut
and 50 degrees from grain. Bearing therefore acts on the angled cut, not on the
grain-parallel support face shown in the NDS compression-taper figure.

## Primary-method disposition

- [NDS 2024 Chapter 4, section 4.4.3 and Figures 4A–4B](https://web-media.awc.org/wp-content/uploads/2021/12/17210008/AWC_NDS2024_20241011_AWCWebsite_Chapter4.pdf)
  applies the sawn-lumber end-notch/taper limits. [NDS 2024 Chapter 3,
  section 3.4.3.1 and Figure 3D](https://web-media.awc.org/wp-content/uploads/2021/12/17210019/AWC_NDS2024_withCommentary_20240718_AWCWebsite_Chapter-3-Design-Provisions-and-Equations.pdf)
  gives the special inner-support-edge depth and inward extension for a
  compression taper, while routing a tension-face taper to the end-notch shear
  equation. For the left compression classification, the geometric mapping
  `d_n = d = 139.7 mm` and `e = 0` is available. Applying that special mapping
  to the tensile right q+ face is unsupported. Treating the complete tension
  bevel literally reaches its zero-depth tip; substituting either the outer
  bearing depth or the bearing-depth difference is not prescribed by these
  provisions. The provisions also do not supply the missing combined local
  stress/fracture check for the direct angled bearing, axial force, biaxial
  shear and bending, and torsion recorded above.
- [AWC 2018 Manual, Figure M7.4-5, printed page 36](https://web-media.awc.org/wp-content/uploads/2022/01/17210413/AWC-2018-Manual-1810.pdf)
  discusses a fire-cut-style I-joist and contrasts it with a historical
  conventional-lumber shear convention for bevels up to 45 degrees. It does
  not define the angle convention in that figure or qualify this solid-sawn,
  directly bearing, combined-load detail under NDS 2024. No I-joist method is
  transferred to the rim.
- [USDA Wood Handbook, Chapter 9, pages 9-4 through 9-5](https://research.fs.usda.gov/download/treesearch/37423.pdf)
  shows that bending of a tapered member can create longitudinal shear and
  transverse normal stress on a sloping face. Its beam equations and example
  do not provide a grade-specific resistance route for this end-bearing solid-
  sawn detail with axial force, biaxial bending and shear, and torsion. The
  [2024 NDS Supplement](https://awc.org/resources/2024-nds-supplement/), Table
  4D, supplies the project's DF-L No. 2 Posts and Timbers values but no
  tension-perpendicular-to-grain design value with which to invent the missing
  comparison. Glulam, engineered-joist and clear-wood values are not substitutes.

Exact blocker: no reviewed primary source both (1) maps this zero-tip full
bevel and angled bearing to local transition/edge stresses for the archived
combined actions and (2) supplies a compatible solid-sawn DF-L No. 2
resistance or fracture interaction. The adjacent 0.017573 MPa tension closes
off the compression-only shortcut but cannot itself be promoted to local cut
stress.

## One finite next geometry study

Study only the square-ended rim with a separately fitted, positively restrained
bearing block already defined in
[the rim resolution](floor-runner-rim-resolution.md). Cut the rim on the
grain-normal plane at local grain station -1183.619990 mm. In side profile,
use the independent bearing-block triangle at
`(-148.513740, 366.797429)`, `(-41.497331, 277.000000)`, and
`(-148.513740, 277.000000)` mm; a nominal 6x6 blank can contain it.

Finite study boundary: establish both fitted contact areas, provide positive
horizontal-thrust and uplift restraint without friction credit, recover one
fresh A12-left demand set for the changed load path, and check rim end bearing,
block compression at angle to grain, block shear/splitting, header bearing and
restraint fasteners using applicable solid-sawn provisions. Stop if no such
restraint route is supported. This option is neither selected nor qualified,
and no demand or passing ratio from the present bevel transfers to it.
