# Full horizontal rim bevel: independent method audit

## Decision

The full horizontal bevel is a materially different geometry from the preserved
compound heel/seat cut. Removing the heel eliminates its re-entrant corner.
That observation does not itself establish an exemption from the current NDS
taper provisions. The compression-taper geometry can be mapped explicitly and
passes the depth limitation. The same mapping cannot be used automatically
when the shortened face carries tension. The ordinary-bevel interpretation
remains an engineering interpretation, not an identified 2024 blanket exception.

This audit changes no selection, CAD, loads, or resistance values. It does not
turn an unresolved method into either a physical failure prediction or a pass.

## Sources and figures inspected

- [NDS 2024 Chapter 4, §4.4.3 and Figures 4A–4B, printed pages 33–34](https://web-media.awc.org/wp-content/uploads/2021/12/17210008/AWC_NDS2024_20241011_AWCWebsite_Chapter4.pdf).
  End cuts on either bending face are subject to a quarter-depth limitation.
  Figure 4B dimensions a compression taper at the inner support edge, rather
  than at the extreme end of its tip. It also limits inward taper extension.
- [NDS 2024 Chapter 3, §3.4.3.1 and Figure 3D, printed pages 20–21](https://web-media.awc.org/wp-content/uploads/2021/12/17210019/AWC_NDS2024_withCommentary_20240718_AWCWebsite_Chapter-3-Design-Provisions-and-Equations.pdf).
  Paragraph (e) explicitly defines the compression-taper remaining depth at
  the inner support edge, perpendicular to member length. Its inward extension
  is `e`. Paragraph (c) routes a tension-face taper to the end-notch equation
  in (a); Figure 3D illustrates a tension notch, not a tension taper. It does
  not grant that route the compression taper's special support-edge definition.
- [AWC 2018 Manual, printed page 36, Figure M7.4-5](https://web-media.awc.org/wp-content/uploads/2022/01/17210413/AWC-2018-Manual-1810.pdf).
  This I-joist discussion contrasts composite joists with a conventional-lumber
  shear convention for bevels up to 45 degrees. The illustration is an I-joist
  fire-cut-style end and does not dimension that angle or establish a 2024
  exemption for a solid inclined member bearing directly on its bevel.

The source figures were visually inspected from the downloaded primary PDFs,
not inferred from extracted text. No copyrighted figure is reproduced here.

## Exact geometry and measurements

Use the YZ grain unit vector `u=(sin40°, cos40°)` and depth vector
`q=(cos40°, −sin40°)`. The full prism is 139.7 mm deep. The end plane is
horizontal at Z277. Its exterior tip is Y−223.862729528; its innermost
intersection is Y−41.497331208. Material retained at successive grain-normal
sections grows from the q− face toward q+; consequently q+ is the shortened
face. Tension previously calculated on q− does not classify this cut.

The header supports the bevel from Y−175.7 to Y−41.497331208. For a point
`(Y,277)` on this bevel, its remaining grain-normal depth is
`d_remaining=(Y+223.862729528) cos40°`, bounded between zero and 139.7 mm.

| Location | Remaining depth |
| --- | ---: |
| Exterior bevel tip | 0 mm |
| Outer actual bearing edge, Y−175.7 | 36.894791 mm |
| Inner actual bearing edge, Y−41.497331208 | 139.7 mm |

The bearing length is 134.202669 mm and the unsupported exterior tail is
48.162730 mm. Their mere existence does not prescribe a requirement to
support the complete bevel. The former scalar `134.202669 cos40° =
102.805209 mm` is the **difference** between the last two depths; it is not
the remaining depth at either support edge.

## Conditional compression-face route

If the actual shortened q+ face is demonstrably a compression face for the
applicable loading, the Figure 3D/4B geometric mapping gives `d_n=d=139.7 mm`
and `e=0`: the first full section passes through the inner bearing edge.
The taper does not extend inward from that section. The quarter-depth
comparison is therefore satisfied, and the compression-notch shear expression
reduces to the ordinary full-section expression, `V_r′=(2/3) F_v′ b d`.

That is a conditional calculation route, not a finding that the whole joint
passes. The depicted NDS support is on a grain-parallel face, whereas this
joint loads the bevel at an angle to grain. Bearing, axial force, local
connection forces, torsion and actual contact distribution still require their
own mechanics. Gross-section compression at one adjacent station is useful
evidence but does not establish a local compression field throughout the cut.

## Tension-face route and the 45-degree statement

The tension-notch equation has a cubic dependence on remaining depth:
`V_r′=(2/3) F_v′ b d_n (d_n/d)^2`. Applying the compression route's
`d_n=d` to a tension taper would silently import an exception not stated for
that route. Conversely, enveloping the entire bevel by a rectangular notch
reaches its zero-depth exterior tip and degenerates. This is a failure of that
literal representation to give a useful qualification, not evidence of zero
physical capacity. Neither the 36.895 mm outer-support section nor the old
102.805 mm projection has been identified as a prescribed tension-taper
equivalent by the reviewed figures.

The cut is 40 degrees from a grain-normal end plane and 50 degrees from grain.
Measuring a bevel from a square end is a plausible interpretation of the
Manual's 45-degree statement, but its text and figure do not specify that
convention. Even accepting 40 degrees does not establish that its historical
shear convention covers this support/load arrangement under NDS 2024.

## Concrete closure criterion

Retain the compression route only with current-case evidence that the q+
cut-face classification and angled bearing/load transfer are applicable.
Where that cannot be established, obtain a method that expressly covers this
full bevel under the actual loads, or use a geometry whose resistance route
is already defined, such as a square rim end with a separately checked fitted
bearing block and positive thrust restraint. A scalar renamed as an NDS check,
an arbitrary stress-concentration factor, or more global load cases alone
does not close the missing local method.

## On-edge 2×6 header hypothesis

Rotating the same nominal 2×6 header to Y[−74.1,−36], Z[137.3,277]
leaves 32.602669 mm of bevel bearing. The minimum remaining depth across
that loaded footprint would be 114.725 mm, exceeding `0.75d=104.775 mm`
by approximately 9.950 mm. It leaves 149.762730 mm of exterior free bevel.
These are geometric results, not an NDS tension-taper mapping.

The reviewed tension provision does not explicitly permit truncating the
notch-equivalent envelope at the outer contact boundary while discarding a
remaining exterior tail. Separately establishing compression in that tail
would strengthen a mechanics-based argument, but it does not make the
loaded-footprint minimum a prescribed NDS dimension. In particular, the tail
still has self-weight and possible connection-induced loads; the support edge
is not a physical free cut. The header rotation is therefore a promising
bearing/connection-layout study, not a source-supported closure of this local
method. Its reduced bearing area and changed header section would also need
current checks. No H3 catalog compatibility is established by this audit;
that requires the manufacturer's exact overhang datum and installation detail.
