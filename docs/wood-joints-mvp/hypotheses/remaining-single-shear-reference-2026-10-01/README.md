# Remaining two-receiver bolts: three-case lateral references

October 1, 2026. This packet implements a source-bound census and conditional
single-shear reference calculation for 52 candidate bolts outside the six
primary-corner and 32 upper-owner axes. It includes the four simple right
post/header bolts. The two right continuous three-receiver side bolts remain
outside this method, as do the twelve retained frame arrangements.

The reviewed candidate and revision stay
`compact-floor-flush-wood-joints-development` /
`led-clearance-2x6-runner-seated-blocks-v1`. Existing A1, A12 and K12 rear
responses supply seven states each. No geometry or response was changed.

## Result and use

| Coverage | Result |
| --- | ---: |
| Source bolt/plane states | 1,092: 52 bolts × three cases × seven states |
| Transverse-to-grain bolts with conditional references | 42 bolts / 882 states |
| End-grain-axis bolts outside the reused method | Ten bolts / 210 explicit null-reference and null-ratio states |
| Receiver-role calculations | Two per eligible state, with mapped six-mode equality |
| Independent closed-form mode comparisons | 10,584 |
| Largest relative mode discrepancy | `9.695710447204099e-16` |
| Eligible axes with a raw scenario ratio above one | One |

The parent independently reproduced the complete producer output and checked
every eligible mode using the separate NDS closed-form implementation in
[parent_verify.py](parent_verify.py). Source RF signs, lateral bases, receiver
identities, case/state coverage, interface datums and separate signed outer
ties are checked by the producer and its pinned source methods. Raw native
files are authenticated; this packet does not independently parse every DAT
RF token or solve another response.

The largest raw comparison occurs on
`bottom_outer/clip_horizontal_bottom_left_1/side_1` at A1 rear full load:
**661.948743 N / 604.790663 N = 1.094508867**, Mode IV. Its simultaneous outer
tie remains separate from lateral yield. The next largest eligible-axis
comparison is `bottom_outer/clip_horizontal_bottom_left_1/rail_2`, also A1
full load, at `0.493282244`. The right post bolts peak at K12 full load:
`post_2` at `0.480264641` and `post_1` at `0.416592574`.

These ratios use an **unadopted 45,000-psi bending-yield scenario**, a smooth
full-body 0.25-inch bearing diameter and conditional DF-L SG 0.50. They are
individual-bolt, unadjusted lateral comparisons. Neither a ratio below one
nor the exception above one is a complete joint pass or adopted failure.
The bottom outer connection needs a supported material, adjustment, group
and complete-joint disposition before acceptance. No favorable duration or
other factor has been chosen to dismiss it.

## Method and applicability

The exact pinned NDS-2024 Chapter 12 PDF is
[AWC's March 2025 Chapter 12 publication](https://awc.org/wp-content/uploads/2026/08/AWC_NDS2024_withCommentary_20250328_WebsiteChapter-12-%E2%80%93-Dowel-type-fasteners.pdf),
SHA-256 `5fc837523ff10acc097a162718700a9b4ba64e627d2b0023439146d42fe4ee2a`.
Printed pages 91–95 supply the six lateral equations, diameter-range
reduction terms, SG/bearing inputs, angle interpolation, bearing lengths and
diameter/Fyb provisions. Table 12A, printed page 101, supplies the full-body
45,000-psi table assumption used as this scenario. Complete applicability is not
established by this arithmetic packet. The full 2026 TR-12 PDF remains
uninspected; no newer-edition qualification is asserted.

The producer reuses the pinned `fea/dowel_yield.py` quadratic single-shear
equations and the existing NDS scenario wrapper. It uses the actual signed
lateral resultant's acute angle to each proposed receiver grain, rounds
the DF-L endpoints to 5,600/4,450 psi, and uses the larger receiver angle in
the existing reduction term. Both main/side role assignments must agree
after swapping the role-labelled modes: Im/Is and IIIm/IIIs; II/IV remain
fixed. An independent Mode IV calculation also checks each assignment.

All selected receivers have one contiguous current-shaft interval, matching
the long-probe interval. Their spans meet at the authenticated plane. Those
modeled lengths are analysis hypotheses, not inspected wood, drill lengths
or purchased bolt-length instructions. Descriptor grains must match the
two pinned current material maps. Native force/identity gates stay unchanged;
the plane-to-CAD datum check uses the declared `1e-6 mm` geometry tolerance.

The ten excluded axes are both bolts in each of:

- `center_post_header_left` and `center_post_header_right`;
- `center_principal_header_left` and `center_principal_header_right`;
- `knee_outer_right_inner_header`.

One receiver's grain runs along each bolt axis. This is the reused transverse
helper's scope boundary, not absence of an NDS end-grain method. Sections
12.3.3.4 and 12.5.2.2 provide a potential main-member end-grain route using
perpendicular bearing and its end-grain factor; that route is not applied
here. The end-grain references and ratios stay null, never zero. Zero lateral
direction is also handled explicitly rather than assigned an angle.

## Reproduction and review

Producer SHA-256:
`5f2a7fdca2ef0c56c661fa10e4122189f8a7a1ae0725062cb8c56d95dd911edf`.
The parent's local full output SHA-256 is
`6551861db1112c91b87c5705bbceb3bb26f55f0d7e70029a74d828519425145e`.
The three-case freeze is
`d4ba1c78eb358d25e32819201e9c59e05d425a06d9e4e5cca3dc09d7139ffd73`.
The required local 54-axis geometry report is pinned to
`64853898bccf71df62119f0977f29aa612b323d436790b370b5616f7b3cb9fe3`.
Raw source, native, STEP and result files remain local; publication contains
code, tests, summaries and the [independent review](independent-method-review.md).

```sh
.venv/bin/python docs/wood-joints-mvp/hypotheses/remaining-single-shear-reference-2026-10-01/produce.py --support-report /tmp/mini-moonboard-remaining-seats-parent-2026-10-01.json > /tmp/mini-moonboard-remaining-single-shear-reference-2026-10-01.json
.venv/bin/python docs/wood-joints-mvp/hypotheses/remaining-single-shear-reference-2026-10-01/parent_verify.py --report /tmp/mini-moonboard-remaining-single-shear-reference-2026-10-01.json
.venv/bin/python -m unittest discover -s docs/wood-joints-mvp/hypotheses/remaining-single-shear-reference-2026-10-01 -p test_produce.py -v
.venv/bin/ruff check docs/wood-joints-mvp/hypotheses/remaining-single-shear-reference-2026-10-01
```

Focused tests cover the published half-inch TR-12 benchmark, signed
direction, asymmetric role permutation, explicit end-grain nulls, invalid
grain-map binding and zero lateral direction. Review corrections and final
replay are recorded separately. The parent oracle was checked against the
rendered NDS equations; its initial k1 exponent transcription was corrected
before the passing full cross-check.

No service/geometry/group/end-grain adjustments, splitting, tear-out,
axial/lateral/bending interaction, washer/contact metal resistance, continuous
three-receiver behavior or stiffness is qualified. All three missing frame
cases and the integrated 47-criterion package remain open. No stock or
hardware was inspected and no physical operation is released.
