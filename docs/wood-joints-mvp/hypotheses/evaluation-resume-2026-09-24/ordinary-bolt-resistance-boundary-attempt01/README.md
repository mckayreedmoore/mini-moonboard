# Conditional bolt-property boundary for the ordinary patch

**Status:** source-bound scope correction, 2026-09-25. This note separates
conditional MVP-E material inputs from current-product proof, NDS lateral
resistance, and complete-joint acceptance. It does not change criteria or the
frozen resistance-preflight results.

## The MVP-E material scenario can use explicit Grade 5 minima

The [MVP-E plan](../../../next-mvp-plan.md) is a conditional engineering
package; physical receiving and prototype observations are MVP-P. The current
[ordinary-hardware sourcing follow-up](../../../current-ordinary-hardware-sourcing-followup.md)
records a K.L. Jack 1/4-20 Grade 5 hex cap-screw/nut candidate, but no hardware
is selected or received. Its product page identifies SAE J429 Grade 5. That
catalog statement is not evidence that any delivered part conforms.

For a bounded engineering scenario, a designer may explicitly require a
1/4-20 UNC cap screw conforming to SAE J429 Grade 5 and add numeric minimum
properties to the project specification. The already-used Value Fastener
[Grade 5 cap-screw technical sheet](https://www.valuefastener.com/documents/products/capscrewgr5-8.pdf)
lists, for Grade 5 hex cap screws from 1/4 through 1 inch, minimum yield
strength 92,000 psi, minimum tensile strength 120,000 psi, and proof stress
85,000 psi. K.L. Jack's own [fastener technical data and charts](https://www.kljack.com/docs/default-source/technical-information/kl_jack_fasteners-technical_data_and_charts.pdf)
label the table SAE J429, Grade 5, and list 2,700 lbf proof load / 3,800 lbf
minimum tensile strength for 1/4-20 UNC cap screws. That is the supplier's
2009/10 catalog, so it is corroboration with an explicit vintage, not a claim
that it is the current SAE table. The Value Fastener sheet identifies
ASME B18.2.1-2012 dimensions but does not identify a J429 revision.

SAE's public [J429 record](https://saemobilus.sae.org/standards/j429_201405-mechanical-material-requirements-externally-threaded-fasteners)
identifies `J429_201405` as the verified revision and states the inch-series
fastener scope, but does not expose the property table. NDS-2024's bibliography
lists J429 (1999). The sources available here therefore do not establish that
the supplier tables reproduce a particular J429 edition's property table.
That is not a blocker to a conditional MVP-E calculation if its input is
spelled out as a **project performance requirement** alongside the chosen
J429 edition: Grade 5, minimum tensile yield 92 ksi, minimum tensile strength
120 ksi, and proof stress 85 ksi. It remains a conditional specification;
it must not be described as proof of the unselected K.L. Jack candidate or
future received parts. The [separate calculation](../ordinary-bolt-steel-reference-attempt01/README.md)
shows the resulting per-bolt material references.

## NDS lateral `Fyb` stays a separate method question

NDS-2024 §12.3.6.2 bases dowel bending yield `Fyb` on yield obtained using
ASTM F1575 bending tests or tensile yield obtained using ASTM F606 procedures.
ASTM F606's active [F606/F606M-26a scope](https://store.astm.org/f0606_f0606m-26a.html)
describes test procedures and says product standards specify property
requirements and applicable tests (§1.2); F606 itself does not assign a
property to this candidate. The Value Fastener sheet's general note says yield
properties are tested on machined specimens only when the testing machine
cannot fully test the parts, but it does not identify an F606 edition or tie
that note to this candidate's lot. NDS-2024's bibliography names
F1575/F1575M-21 and F606/F606M-21; ASTM's current records list F1575/F1575M-24
and F606/F606M-26a. For a normative test-derived route, state whether the
NDS-referenced editions or later editions with an explained basis are used.
Thus the 92 ksi Grade 5 value is usable as a conditional direct steel input,
while it does not, by itself, demonstrate the NDS test-derived `Fyb` route.

NDS Commentary Appendix I describes an approximate bolt estimate
`Fyb ≈ (Fy + Fu) / 2`. With the conditional minima above, this gives
`Fyb ≈ 106 ksi`. This is an implementable, source-based **commentary estimate**
for a clearly labeled modeling scenario; it is not a product-standard minimum,
a measured bending result, or a guaranteed lower bound. Do not report it as
normative/test-derived NDS `Fyb` or use it to close the Fyb criterion without
an explicit method review. The NDS Commentary / AWC TR12-2026 `45 ksi` example
is limited to bolt/lag-screw diameters `D ≥ 3/8 in` and does not transfer to
the present 1/4-in case. The AWC Commentary source checked here is its official
2024 Appendix PDF (repository copy SHA-256
`99b0a54e7133b3cf6dd156d8fe864c1717c951487bf5baa99c34da9a68a6bbb7`); the
NDS §12 source is the pinned official Chapter 12 PDF (SHA-256
`5fc837523ff10acc097a162718700a9b4ba64e627d2b0023439146d42fe4ee2a`).

## What still needs product geometry, additional resistance sources, or demands

- ASME B1.1's declared thread class can support a conditional standard
  thread-root geometry. Using smooth-shank diameter or the NDS full-body-`D`
  exception requires thread-bearing extents in each member. The current 6.35 mm
  CAD cylinder is an occupancy envelope and does not supply those extents. A
  root-diameter-only scenario can be evaluated without receiving inspection;
  it cannot be mistaken for the actual thread placement.
- The proposed Grade 5 nut is separately listed to SAE J995, but no current
  1/4-20 Grade 5 proof/strip value or thread-engagement resistance basis is
  pinned here. A bolt's J429 grade does not define nut strength. A conditional
  nut calculation needs the applicable J995 minimum or an explicit nut
  performance requirement, its test basis, and a supported engagement length.
- ASME Type A Wide washer dimensions establish geometry, not steel yield,
  bending, or spreading resistance. A conditional washer check needs specified
  washer material/mechanical minima and a supported plate/bearing model.
- Fresh demands, validated four-bolt force sharing, complete load-path
  resistance, member/group checks, and any tension/shear interaction remain
  separate. No per-bolt material reference is a joint capacity or pass.

The ordinary-patch preflight's delivered-Fyb evidence requirement is too narrow
for a conditional MVP-E scenario: the scenario should accept a specified
Grade 5 material basis while preserving a separate `delivered_conformance`
status for MVP-P. Its resistance calculation still needs a reviewed choice
between the test-derived NDS `Fyb` route and the clearly labeled Commentary
estimate. This note makes no ledger edit and closes no criterion.

## Source trail

- Value Fastener, [Grade 5 / Grade 8 cap-screw sheet](https://www.valuefastener.com/documents/products/capscrewgr5-8.pdf),
  checked online 2026-09-25: 1/4–1-in Grade 5 min yield 92 ksi, min tensile
  120 ksi, proof stress 85 ksi; dimensional table cites ASME B18.2.1-2012.
- K.L. Jack, [fastener technical data and charts](https://www.kljack.com/docs/default-source/technical-information/kl_jack_fasteners-technical_data_and_charts.pdf),
  current hosted PDF, catalog marked 2009/10: SAE J429 Grade 5 and 1/4-20
  proof/tensile loads 2,700 / 3,800 lbf. This is not lot test data.
- [Current 48-axis ordinary hardware basis](../../../current-ordinary-hardware-basis.md),
  [current sourcing follow-up](../../../current-ordinary-hardware-sourcing-followup.md),
  and [representative resistance method](../../../representative-fastener-resistance-method.md).
- [NDS-2024 Chapter 12](https://awc.org/wp-content/uploads/2026/08/AWC_NDS2024_withCommentary_20250328_WebsiteChapter-12-%E2%80%93-Dowel-type-fasteners.pdf),
  [NDS-2024 Appendix](https://web-media.awc.org/wp-content/uploads/2021/12/17210019/AWC_NDS2024_withCommentary_20240719_AWCWebsite_Appendix.pdf),
  [SAE J429_201405 record](https://saemobilus.sae.org/standards/j429_201405-mechanical-material-requirements-externally-threaded-fasteners),
  [ASTM F1575/F1575M-24](https://store.astm.org/f1575_f1575m-24.html),
  [ASTM F606/F606M-26a](https://store.astm.org/f0606_f0606m-26a.html),
  and [ASME B1.1-2024](https://www.asme.org/codes-standards/find-codes-standards/b1-1-unified-inch-screw-threads-un-unr-thread-form).
