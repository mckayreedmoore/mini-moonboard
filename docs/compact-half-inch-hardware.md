# Purchasable half-inch hardware for the compact leg trial

Research date: 2026-09-13. This is a procurement and dimensional assessment,
not a release of the joint or a certificate for delivered hardware.

**A standard SAE J429 Grade 5 half-inch bolt provides a documented 92 ksi
tensile-yield specification. A 90 ksi Fyb calculation is therefore a defensible
specified-material candidate under the NDS tensile-yield route, conditional on
the applicable ASTM F606 basis and supplied material conformity.** No Grade 8
upgrade is needed merely to reach 90 ksi. Existing calculations using 45 ksi
remain historical; adopting 90 ksi requires explicitly rerunning the affected
yield modes. Mode II contains no fastener bending-yield term and cannot improve
from this change alone.

## Concrete catalog stack

| Part | Purchasable reference | Catalog facts relevant to this assessment |
| --- | --- | --- |
| Bolt | [Bolt Depot 407](https://boltdepot.com/Product-Details?product=407) | Zinc-plated SAE J429 Grade 5, 1/2-13 × 8 inches, partially threaded, ASME B18.2.1. Length tolerance +0/−0.18 inch; thread length **minimum** 1.5 inches. |
| Nut | [Bolt Depot 2573](https://boltdepot.com/Product-Details?product=2573) | Zinc-plated Grade 5, SAE J995, 1/2-13, ASME B18.2.2; height 0.427–0.448 inch; minimum across-flats dimension 0.736 inch. |
| Two washers | [Bolt Depot 15025](https://boltdepot.com/Product-Details?product=15025) | Zinc-plated Grade 5 USS, ASME B18.21.1; OD 1.368–1.380 inches, ID 0.547–0.577 inch, thickness 0.086–0.132 inch. |

These are catalog-listed products, not a stock reservation. The current
`mini_moonboard/compact_thick_frame.py` uses an 8-inch bolt, 7-inch wood grip,
two 0.125-inch washers, and an 11.5316 mm nut. The catalog nut maximum is
11.3792 mm, slightly shorter than modeled. The washer outside diameter agrees
nominally, but the catalog tolerances do not guarantee the modeled washer
thickness or hole size.

## Strength basis and its limit

[NDS §12.3.6.2](https://awc.org/wp-content/uploads/2021/10/AWC_NDS2018-withCommentary_20210928_AWCWebsite_Chapter12.pdf)
permits Fyb from ASTM F1575 bending testing or tensile yield derived using ASTM
F606 procedures. These are alternative routes; a direct bolt bending test is
not the only permitted route. [ASTM's F606 scope](https://store.astm.org/standards/f606)
includes yield determination for externally threaded fasteners and machined
specimens. [Portland Bolt's J429 mechanical-property table](https://www.portlandbolt.com/technical/faqs/j429-strength-requirements/)
gives Grade 5, 1/4 through 1 inch, minimum tensile yield 92 ksi, proof stress
85 ksi and tensile strength 120 ksi. Grade 8 minimum tensile yield is 130 ksi.
Proof stress and ultimate tensile strength must not be substituted for Fyb.

The catalog identifies J429 material, but supplies no inspected lot certificate
or explicit F606 yield report on the product page. Accordingly, specify Grade 5
conformity and the F606-compatible yield basis for a 90 ksi design assumption;
record it as specified, not measured. A delivered certificate or supplier
documentation can establish that traceability. This research does not assert
that every individually purchased bolt was yield-tested.

## Thread bearing and nut seating

[NDS §12.3.7.2](https://awc.org/wp-content/uploads/2021/10/AWC_NDS2018-withCommentary_20210928_AWCWebsite_Chapter12.pdf)
allows nominal diameter for a full-body threaded fastener when threaded bearing
occupies no more than one quarter of the bearing length in the member holding
the threads. Otherwise use the root diameter or a detailed threaded-section
analysis. Here each member is 3.5 inches thick: the limit is **0.875 inch
(22.225 mm) per member**.

With modeled washers and exactly 1.5 inches of threads, the 8-inch bolt has
6.5 inches of nominal unthreaded length from its bearing face. Thread bearing
in the second member is 7.125 − 6.5 = 0.625 inch (17.86%); the first member
contains none. Including the shortest catalog bolt and thickest head washer,
but still assuming exactly 1.5 inches of threads, gives 0.812 inch (23.2%).
That leaves only 0.063 inch (1.6002 mm) for extra thread length or transition.
Because the catalog specifies a **minimum**, not maximum, thread length, these
calculations establish nominal feasibility, not guaranteed full-diameter use.

A concrete acceptance check is to measure the full-body shank through the
thread transition. With a 0.132-inch head washer and 7-inch actual wood grip,
the first reduced/transition section must be at least **6.257 inches
(158.9278 mm)** from the under-head bearing face. Use actual member lengths and
washer thickness in this threshold; conservatively count the transition with
the threaded region. Independently ensure the nut reaches its bearing washer
on fully usable threads before contacting runout, and retains full formed-thread
engagement at the bolt tip.

The shortest bolt, two thickest catalog washers, and tallest catalog nut leave
7.82 − 7 − 0.264 − 0.448 = **0.108 inch (2.7432 mm)** beyond the nominal nut
face. This is a useful fit allowance, not a guarantee concerning tip chamfer
and actual formed-thread engagement. A 9-inch bolt with an ordinary 1.5-inch
thread length starts its threads at 7.5 inches, beyond the approximately
7.25-inch nut bearing face; it cannot simply replace the 8-inch bolt without a
different documented thread length or an assessed spacer stack.

## Completed current hardware comparison

Do not transfer the existing 0.125-inch washer bending result to every 15025
washer. Its 0.086-inch catalog minimum increases a simple plate bending-demand
ratio by approximately (0.125/0.086)² = **2.113**, before accounting for the
larger permitted bore and other dimensions. The current assessment uses catalog lower-bound
dimensions and the stated washer-yield assumption. The supplier's washer grade label alone does not
establish a 92 ksi plate-yield input.

The selected [spliced-knee assessment](compact-splice-study.md) completes that
comparison with its own six assembled load cases, 90 ksi Fyb, Cd = 1, and
catalog-minimum washer dimensions with the explicit 33 ksi washer-yield
assumption. Every listed conditional criterion passes. The preceding compact
three-bolt trial remains historical; no earlier failure is relabeled. Delivered
hardware must still meet the specified shank, thread and material conditions.
