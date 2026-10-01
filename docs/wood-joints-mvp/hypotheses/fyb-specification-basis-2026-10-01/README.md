# Quarter-inch bolt bending-yield source disposition

Checked October 1, 2026. This is a source interpretation for the conditional
wood-joint development lane. It adopts no resistance, selects no hardware,
and supplies no joint pass. The reviewed model and existing evidence remain
unchanged.

## What the specification permits

NDS 2024 §12.3.6.2, printed page 95 / Chapter 12 PDF page 17, bases the
fastener bending-yield strength used for lateral reference value `Z` on
yield derived from ASTM F1575 methods **or** tensile yield derived from ASTM
F606 procedures. It does not require a new delivered-bolt bending test for
every conditional analytical scenario. ASTM F606 supplies test methods;
its public scope does not assign a product's material properties.

Nonmandatory NDS Appendix I.4, printed page 185 / Appendix PDF page 20,
describes evaluation of tensile-test data to estimate bending yield for
short, large-diameter fasteners and gives the empirical approximation
`Fyb ≈ (Fy + Fu)/2`. This equation is in the **nonmandatory Appendix**, not
the separately published Commentary. The earlier
[washer/bolt method note](../corner-washer-method-investigation-2026-10-01/source-note.md)
called it Commentary; this note corrects that attribution without rewriting
the evidence pinned by existing calculations.

For an explicitly hypothetical quarter-inch J429 Grade 5 material with
specified `Fy = 92 ksi` and `Fu = 120 ksi`, the approximation gives
`Fyb_estimate = 106 ksi`. That is a conditional empirical estimate. Neither
the normative clause nor the Appendix establishes 106 ksi as a guaranteed
minimum, a lower bound, or the yield of a particular listed or received
bolt. It is also not a source basis for simply setting `Fyb = Fy = 92 ksi`.

The Appendix's Table I.1, printed page 186 / PDF page 21, lists 45 ksi for
bolts and lag screws of diameter **at least 3/8 inch** (and drift pins),
with a Grade 1 example. That row does not establish a quarter-inch lower
bound. Its Grade 1 example also demonstrates why averaging specified minima
is not itself proof of a guaranteed bending-yield minimum.

## What this resolves and leaves open

The [upper-block packet](../upper-block-strength-2026-10-01/README.md)
already evaluates the 106 ksi scenario and its duration/Fyb sensitivities.
Those calculations need not wait for a new test on delivered hardware.
They remain conditional comparisons; this source disposition does not
promote them to adopted resistance or replace their existing sensitivities.

An adopted product-specific NDS input still needs an applicable, reviewed
basis tying the chosen fastener to F1575 bending-yield data or F606
tensile-yield data and its evaluation into `Fyb`. A product's standard
conformance may support such a route if the pertinent requirements and
evaluation are established; a new specimen test is not assumed to be the
only route. The full J429-2014 test clauses were not available to this
review, so J429 conformance alone has **not** been verified here as an F606
tensile-yield datum. An indexed government-hosted copy was located but
returned HTTP 403; its search excerpt is not treated as an inspected clause.

The direct Grade 5 `Fy` scenario remains useful for a separate steel
first-yield check using same-state axial force, shear and moment at the
actual section. That check is distinct from NDS lateral-yield resistance;
the scalar washer tie alone is insufficient. No material property resolves
the current missing bearing/contact, prying, thread location, splitting or
complete-joint evidence.

## Inspected primary sources

The two official AWC PDFs were read from the upper owner's local source
cache; their exact bytes were authenticated. Raw PDFs remain local.

| Source | Inspected provision / local SHA-256 |
| --- | --- |
| [NDS 2024 Chapter 12](https://awc.org/wp-content/uploads/2026/09/AWC_NDS2024_withCommentary_20260911_Website_Chapter-12-Dowel-Type-Fasteners.pdf) | §12.3.6.2, printed p. 95. `53f6ec05dfd1ceabeccd4d6e88c342111678d3da4631ee7b482b706f77c1780f` |
| [NDS 2024 Appendix](https://awc.org/wp-content/uploads/2026/09/AWC_NDS2024_withCommentary_20260911_Website-Appendix.pdf) | Nonmandatory I.4 and Table I.1, printed pp. 185–186. `1fa2bcf52803b1bbed8ea30cf13551dd5f76c90bf110ac475b401f81d116ec31` |
| [ASTM F1575/F1575M-24](https://store.astm.org/f1575_f1575m-24.html) | Public scope covers bending-yield moment and `Fyb` for threaded dowel-type fasteners. |
| [ASTM F606](https://store.astm.org/standards/f606) | Public scope describes mechanical test methods; it does not assign the candidate's properties. |
| [SAE J429-2014 publisher record](https://saemobilus.sae.org/standards/j429_201405-mechanical-material-requirements-externally-threaded-fasteners) | Edition metadata only; full test clauses were not inspected. |

The conditional 92/120 ksi size-band inputs are documented in the existing
[hardware source screen](../hardware-material-specification-2026-09-30/fasteners.md).
They are assumptions here, not a newly inspected official J429 table or a
claim about exact SKU conformance. Receiving and physical observations remain
outside this analytical disposition; checklist Actual/Disposition cells stay
blank. Independent source review is recorded separately.
