# PB01 direct cross-dowel connection screen

21 September 2026. **PARK: geometry qualification route only.** This extends the
[CD-01 trial](simple-pb01-cross-dowel-trial.md) and
[retail follow-up](simple-pb01-cross-dowel-retail-followup.md). It does not rerun
their CAD collision checks, change the PB01 candidate, select hardware, or
release drilling or structural use. No supplier was contacted.

## Retail fact and missing drawing

[Lowe's Hillman 880543 listing][hillman] identifies a factory 1/4-20
zinc-plated steel barrel nut, item 137362. In a [Hillman customer-service
answer hosted by Lowe's][answer], Hillman states nominal outside diameter
0.394 in (10.0076 mm) and overall length 0.630 in (16.002 mm). The listing
says the threaded shaft passes through the side of the barrel. It does not
dimension the cross-hole axis from either end, complete internal-thread span,
chamfers, tolerances, material strength, proof load, or installed-joint
resistance. No part-specific manufacturer drawing establishing these fields
was found in the public Hillman/Lowe's/Home Depot material checked. The retail
terms “steel” and “strong joint” are not capacity evidence.

Other manufacturers show why centering cannot be assumed. [JET PRESS FCD008][jet]
lists a separate M6, 10 × 16 mm central cross dowel with an 8 mm offset;
[SISO 12.07.044-0][siso] lists a separate M6, 10 × 16 mm product with 10/6 mm
end distances. They are **analogies**, not Hillman specifications or
interchangeable 1/4-20 parts. The bounded 6–10 mm interval below is a
falsifiable sensitivity: an 880543 outside it invalidates this interval and
must be screened from its measured offset.

## One PB01 connection pose

The existing CD-01 pose has two +X bolts, one barrel from each opposite rail
T face, a 38.1 mm rail T thickness, and a fixed bolt/thread axis 19.05 mm
from its respective entry face. The rail end and principal remain the existing
butt connection; no lap joint or new fabricated part is introduced. CD-01
reports the 108.1 mm outside-seat-to-axis wood path and uses a **trial** 127 mm
under-head bolt. Those are model inputs, not a qualified purchased bolt stack.

For barrel end-to-axis offset `a`, body length `L`, and body diameter `D`:

`recess = 19.05 − a`; `wood beyond body = 38.1 − recess − L`.

With Hillman's **nominal** `L = 16.002 mm`, `a = 6–10 mm` requires a recess
of **13.050–9.050 mm**, leaving at least **9.048 mm** nominal wood behind the
barrel. Nominal metal beyond a 1/4-in thread major radius at both barrel ends
is at least `min(a, L−a) − 3.175 = 2.827 mm` over that interval. This is
geometric stock only; it is not a section or thread strength calculation. The
prior CD-01 CAD clearance result applies only to its own 10 × 16 mm trial
solids. Delivered OD, bore clearance, tolerances, screw clearances, and access
must be checked again if this route advances.

Without a washer, a 127 mm trial bolt projects `127 − 108.1 = 18.9 mm` beyond
the barrel thread axis, or **13.8962 mm** past its nominal far outside surface
along X. Washer thickness reduces that projection; this apparent overrun does
not establish engagement and requires a compatible hole with tip clearance.
The [screen](../../scripts/simple_pb01_cross_dowel_geometry_screen.py) accepts
measured body dimensions, end-to-axis offset, actual bolt under-head length,
washer stack, complete bolt-thread interval, complete barrel-thread interval
along X, available hole depth, and required tip clearance. It reports overlap
of *complete* threads and whether the tip clears the hole end. Its positive
`geometry_fit` means only positive geometric overlap and stated tip clearance.
It cannot set the minimum engaged length or prove thread stripping resistance.
The test's example thread spans are illustrative inputs, not measured 880543
or bolt properties. Bolt-thread distances are from the head underside; the
barrel-thread interval is measured along X from its cross-hole axis, negative
toward the principal. Hole depth is measured from the outside wood seat.

[AWC TR12][awc] supplies lateral dowel-connection equations and lists fastener
tension, bearing, shear, spacing, group action, member strength, fabrication,
and tolerance as separate design considerations. It supplies no 880543
barrel-thread, transverse metal, or wood anchorage value. The [US Forest
Service dowel-nut study][fpl] tested different, much larger hardware and wood
specimens; its loads cannot be assigned to this PB01 part. No public
part-specific strength or joint rating was found for Hillman 880543, so no
allowable load or utilization is calculated here.

Run the focused check:

```sh
uv run --no-sync python -m scripts.simple_pb01_cross_dowel_geometry_screen
uv run --no-sync pytest -q tests/test_simple_pb01_cross_dowel_geometry_screen.py
```

**Selection gate:** identify the delivered 880543 batch and measure low/high
body OD, length, and axis offset from a marked insertion end; obtain the
complete internal-thread interval, compatible bolt's complete-thread interval,
under-head length, washer seat, and supported bore/tip-clearance limits. Screen
worst-case combinations for both opposite-face barrels, then repeat physical
clearance and assembly/removal checks. Separately establish a part-specific
barrel metal/thread resistance basis, required effective engagement, wood
bearing and splitting/end tear-out, bolt and washer resistance, and changed
PB01 load distribution/contact/stiffness. A measured fit alone cannot supply
steel strength. If no applicable part-specific strength evidence or bounded
qualification test is available, this alternative stays parked. Nothing here
transfers the corner-block result or authorizes fabrication, purchase, or
structural release.

[hillman]: https://www.lowes.com/pd/Hillman-20-x-5-8-in-Slotted-Drive-Zinc-plated-Barrel-Nut/3012559
[answer]: https://www.lowes.com/questions/hillman-880543-specialty-nuts/3012559/0d07d7d4-94c9-59c7-b300-30a2fd0be7bd
[jet]: https://www.jetpress.com/component-and-fastener-products/cross-dowels-barrel-nuts/FCD008
[siso]: https://siso.dk/products/furniture-fittings/knock-down-fittings/screws-bushings-nuts/cross-dowels
[awc]: https://awc.org/wp-content/uploads/2021/12/AWC-TR12-1510.pdf
[fpl]: https://research.fs.usda.gov/treesearch/6003
