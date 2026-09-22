# 2024 NDS applicability to the owner barrel-nut joints

**Methods finding, not a capacity or build approval.** The furniture-style
machine bolt runs through one wood member and threads into a transverse steel
cross-dowel buried in the other. The dowel is not an exterior nut/washer or a
continuous bolt through two wood side plates. The 2024 NDS supplies useful
*constituent* wood and lateral-bolt checks, but its ordinary bolted-connection
yield equations and placement tables do **not directly rate this complete
bolt–barrel–wood joint**, especially its axial/tension load path. That is an
applicability judgment from the stated NDS models, not a claim that the NDS
prohibits a separately justified connection. The clause references below are
to official [2024 Chapter 11][ch11], [Chapter 12][ch12], [Appendix E][app-e],
the [2024 Supplement][supplement], and [March 2026 errata][errata]. Do not
import 2018 values or turn a generic bolt grade into joint capacity.

| Item | Direct 2024 NDS coverage? | Boundary for this joint |
| --- | --- | --- |
| Ordinary bolt installation | **No, as drawn:** §12.1.3 requires qualifying bolt details and head/nut-side bearing washers. | The buried barrel replaces the exposed nut-side stack. §§11.1.1.3 and 12.1.8 require justification for variants. |
| Lateral bolt yield and wood embedment | **Conditional submodel:** §12.3.1/Tables 12.3.1A–B require a real shear plane, contacting faces, normal-to-axis load and §12.5 geometry; §12.3.3 supplies bearing inputs. | Prove shank/thread bearing lengths, diameter, grain angle, bending-yield strength and no unmodeled gap. A lateral `Z` does not rate barrel anchorage; [AWC's TR12 gap FAQ][gap-faq] states its hinge assumption. |
| Bolt end/edge/row geometry | **Direct for a qualifying lateral dowel:** §§12.1.2, 12.1.3.4, 12.5.1; Tables 12.5.1A–D. | Check each wood member and signed load. Bolt-axis minimums do not establish safe cover, splitting or tear-out at the transverse barrel bore or head recess. |
| Along-bolt axial force | **No barrel-joint resistance equation:** §12.3.9 separates oblique loads and requires adequate axial bearing. | §12.2 wood-embedded screw withdrawal and round-head pull-through values are not steel-thread/barrel capacities. Check the full axial chain separately. |
| Barrel and surrounding wood | **No complete-joint yield mode:** §12.3.1 models a continuous dowel across member shear planes, not a cross-drilled nut buried in one member. | §§11.1.2–11.1.3 and Appendix E inform member/eccentric/net-section checks; barrel-specific bearing and breakout remain separate. |
| Metal, group action, reuse | **Not a complete rating:** NDS group rules presuppose applicable individual joints. | Independently check bolt, threads, barrel, washer, group sharing, looseness and repeated demounting. No unproved clamp-friction credit. |

## Implementable evidence route

1. Freeze **one** joint family at a time: controlled bolt, barrel and washer
   geometry/material/tolerances; delivered thread length and engagement; wood
   species/grade/moisture; grain directions; all bores/counterbores and contact
   faces. The viewer's provisional dimensions are not shop dimensions.
2. For each station and signed design case, draw a free body and resolve load
   along/across the bolt and barrel axes, including eccentric moments. Prove
   which surfaces actually transfer force without relying on clamp friction.
   Record actual minimum wood cover and all altered net sections from the
   kerf-right CAD, including the recessed outer headers.
3. Apply **2024** NDS §12.3.1 and Tables 12.5.1A–D only to a demonstrably
   matching lateral bolt/shear-plane subcase. Use 2024 wood values and all
   applicable adjustments; check members under §§11.1.2–11.1.3 and the
   corrected §3.4.4.1 reference in the [errata][errata]. For barrel-body
   bearing, use an explicitly justified local mechanics model or measured
   input; do not call the bolt's `Z` a barrel/wood capacity.
4. Independently establish the metal and axial chain: bolt root and combined
   stress, thread engagement/strip, barrel wall and flexure, washer/head
   bearing, wood compression at the cross-bore, split/breakout/net-section and
   group interaction. Document the controlling *same-case* mode; a separate
   high bolt tensile rating cannot eliminate weaker wood or barrel modes.
5. Where controlled material properties and defensible geometry-specific
   mechanics cannot close those checks, use **complete-joint** tests in the
   actual member, grain, hole, washer and hardware configuration, for both
   load directions and combined actions; include installation tolerance,
   moisture/conditioning and repeated assembly cycles. A qualified test
   protocol, specimen count, characteristic-value method, safety/adjustment
   basis and acceptance criteria would have to be set *before* testing; no
   particular external test standard is adopted here. Test results alone are
   not design values.

Until the full path and all required frame load cases are closed, this is
research only: no capacity claim, hardware purchase recommendation, drilling,
fabrication or climbing release. No manufacturer contact was made.

[ch11]: https://web-media.awc.org/wp-content/uploads/2021/12/17205958/AWC_NDS2024_20250124_AWCWebsite_Chapter11.pdf
[ch12]: https://awc.org/wp-content/uploads/2026/08/AWC_NDS2024_withCommentary_20250328_WebsiteChapter-12-%E2%80%93-Dowel-type-fasteners.pdf
[app-e]: https://web-media.awc.org/wp-content/uploads/2021/12/17210019/AWC_NDS2024_withCommentary_20240719_AWCWebsite_Appendix.pdf
[supplement]: https://awc.org/resources/2024-nds-supplement/
[errata]: https://awc.org/wp-content/uploads/2026/03/2024-NDS-Errata-and-Addenda-03.23.26.pdf
[gap-faq]: https://awc.org/faq/does-technical-report-12-general-dowel-equations-for-calculating-lateral-connection-values-assume-the-connector-does-not-deform-in-the-gap/
