# Supplemental EC5 splitting — source gap and applicability attempt01

Status: **source-gap decision; no criterion method implemented**. No current
splitting demand, resistance, capacity, ratio, pass, or failure is produced.
`supplemental_EC5_splitting` remains pending. The independent worked-example
arithmetic is only a formula transcription check and uses no candidate input.

## Decision

Do not implement a splitting evaluator from the sources presently bound to
this project. The first-generation EN 1995-1-1 candidate is identifiable as
§8.1.4, corrected by EN 1995-1-1:2004/AC:2006, but the project has not selected
an EC5 edition, jurisdiction, National Annex, or explicitly non-regulatory
analytical scenario. Its current structural basis is the separate NDS route.
The accessible primary correction supplies only specified corrections to the
first-generation clause. The JRC material reproduces/explains other clause
text but is training material, not the complete normative clause and figure.
The first-generation rule is limited to softwood and the arrangement in
Figure 8.1; the available sources and current evidence do not establish that
the candidate's changed bolted solid-wood joints fit it.

The [official BSI record for BS EN 1995-1-1:2025][bs2025] identifies the
second-generation edition as published and current. The European Commission
JRC's [second-generation transition page][jrc-transition] states that
definitive text was to be distributed to National Standards Bodies by
2026-03-30, with national publication by 2027-09-30 and withdrawal of
conflicting first-generation national standards by 2028-03-30. The available
JRC 2025 presentation gives a clause outline for brittle failures but not the
normative equations, definitions, figure, applicability rules, or design
conversion. BSI separately describes the UK first-generation/second-generation
coexistence period; that UK-specific path cannot select an edition for this
project, which records no governing jurisdiction.

The source gap is therefore not a lack of a plausible equation. The corrected
first-generation characteristic expression is transcribable, and an
independent arithmetic check matches a published example. What remains
unresolved is the exact governing/applicable clause text and proof that its
specified connection geometry, force definition, member scope, and design
conversion fit each candidate splitting path. A familiar formula alone does
not resolve those gates.

## Source and applicability findings

The primary [CEN 2004/AC:2006 corrigendum][cen-ac], retrieved from the Swiss
SIA standards mirror, corrects the first-generation §8.1.4 Eq. (8.4) and
associated definitions. Its correction is limited; it is not the full
standard. The exact corrected characteristic expression is:

```text
F90,Rk = 14 b w sqrt(he / (1 - he/h))
```

The equation is stated for softwoods and the arrangement shown in Figure 8.1.
The first-generation §8.1.4 load comparison and surrounding applicability
text are reproduced in the official [JRC 2008 training presentation][jrc2008]
and the separately authored ICE Designers' Guide. Neither replaces the full
normative clause, and the JRC deck is explanatory material. No permitted
current-project source here provides a complete authenticated Figure 8.1 and
§8.1.4 package tied to a selected edition and National Annex.

The current [criterion map][criteria-map] keeps the row open and names exact
group/end/edge geometry, member grain, holes/cuts, and signed cross-grain
action as required evidence. It states no splitting producer exists. The
[coverage register][coverage] says no current splitting calculation or
applicability decision exists. The current attachment-topology snapshot
enumerates connections and member pairs, but it is not an accepted splitting
action record. No accepted current per-member shear actions `Fv,Ed,1` and
`Fv,Ed,2`, loaded-edge classification, or complete applicable finished-section
manifest is bound here. The existing [wood limit-state basis][basis] and
[previous splitting screen][prior-screen] likewise leave method applicability
open; they remain untouched.

For a connection represented by §8.1.4, the design decision depends on the
specified two-sided connection shear forces and the corresponding splitting
resistance, not an arbitrary sum of bolt cross-grain force components. The
current multi-group block, cleat, and through-bolted-member topologies cannot
be mapped to that representation by naming one closest loaded edge. The
available evidence also does not establish the selected material/product
class, service/load-duration conversion, `kmod`, `gammaM`, or the exact
selected National Annex. No alternative NDS or generic fracture expression is
substituted.

## Independent published-example arithmetic

The independently authored *Designers' Guide to Eurocode 5: Design of Timber
Buildings*, Example 8.1 (Porteous and Ross, ICE Publishing, 2013, p. 101),
provides a worked first-generation softwood connection example. The
[JRC book record][ice-guide] verifies its bibliographic identity; the guide is
a secondary worked example, not normative standard text. Its values are used
only as an independent arithmetic check:

| Input | Published example value |
| --- | ---: |
| Member height, `h` | 120 mm |
| Loaded-edge distance, `he` | 60 mm |
| Effective thickness, `b` | 2 × 50 mm = 100 mm |
| Fastener factor, `w` | 1 |
| Design shear, `Vd` | 8.9 kN |
| Example factors | `kmod = 0.8`, `gammaM = 1.3` |

An independent 40-digit Decimal calculation of the corrected Eq. (8.4) gives
`F90,Rk = 15.3362316101 kN`, then the example's conversion gives
`F90,Rd = 9.4376809909 kN` and `Vd/F90,Rd = 0.9430282724`. These round to the
guide's published `15.34 kN`, `9.44 kN`, and `0.94`. The reproducible values
are in [`independent-example-arithmetic.json`](independent-example-arithmetic.json).
This checks arithmetic only: it does not validate the normative scope,
select factors for this project, establish Figure 8.1 applicability, or
qualify any candidate connection.

## Required evidence before another method attempt

The exact next consumer is WJ-08/T06 for `supplemental_EC5_splitting`, after
the coordinator supplies all of the following:

1. A selected EC5 edition and design route, including jurisdiction and
   applicable National Annex if a compliance claim is intended; or a clearly
   named, non-regulatory analytical scenario that does not imply EC5
   compliance.
2. Authenticated, version-matched primary text for the selected clause, its
   figure and definitions, design conversion clauses, and applicable errata.
   If using second-generation EN 1995-1-1:2025, first-generation Eq. (8.4) must
   not be carried forward without explicit support from the new text.
3. For every affected host/member path, a source-bound mapping to the chosen
   clause's exact geometry and loading arrangement, including finished
   dimensions, holes/cuts, grain direction, loaded edge, and the two-sided
   design shear actions required by that method.
4. A verified material/product scenario and all method-required design-value
   conversion factors. Current values must come from current, independently
   accepted evidence.
5. If the exact EC5 arrangement does not cover a changed joint, an
   authoritative replacement method with an independent worked/known-answer
   example and a demonstrated scope match. Unsupported joints stay pending.

No current candidate method result or criterion disposition changes here. The
47-criterion register and this splitting criterion remain pending. No native
solver was run, and no geometry, material assignment, method map, or current
capacity record was edited.

## Reproduction

The independent arithmetic results are recorded in
[`independent-example-arithmetic.json`](independent-example-arithmetic.json).
The checked source identities, repository digests, and source-status limits
are in [`source-pins.json`](source-pins.json). Artifact digests and checks are
in [`terminal-hashes.json`](terminal-hashes.json).

Run the artifact and known-answer checks from the repository root:

```sh
python3 -m json.tool docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-ec5-splitting-source-gap-attempt01/source-gap-decision.json >/dev/null
python3 -m json.tool docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-ec5-splitting-source-gap-attempt01/source-pins.json >/dev/null
python3 -m json.tool docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-ec5-splitting-source-gap-attempt01/independent-example-arithmetic.json >/dev/null
```

The separate 40-digit Decimal recomputation for the published example is:

```python
from decimal import Decimal, getcontext
getcontext().prec = 40
b, he, h, w = map(Decimal, ("100", "60", "120", "1"))
f90_rk = Decimal(14) * b * w * (he / (1 - he / h)).sqrt()
f90_rd = Decimal("0.8") * f90_rk / Decimal("1.3")
ratio = Decimal("8900") / f90_rd
print(f90_rk / 1000, f90_rd / 1000, ratio)
```

This calculation is limited to the published example inputs. It is not a
reusable method evaluator and does not accept candidate data.

[bs2025]: https://knowledge.bsigroup.com/products/eurocode-5-design-of-timber-structures-general-rules-and-rules-for-buildings
[jrc-transition]: https://eurocodes.jrc.ec.europa.eu/second-generation-eurocodes
[cen-ac]: https://cms.sia.ch/en/api/getMedia/559
[jrc2008]: https://eurocodes.jrc.ec.europa.eu/sites/default/files/2022-06/EN1995_3_Dietsch.pdf
[ice-guide]: https://eurocodes.jrc.ec.europa.eu/publications/designers-guide-eurocode-5-design-timber-buildings-en-1995-1-1
[criteria-map]: ../../../criteria-method-map.md
[coverage]: ../../../current-criteria-coverage.md
[basis]: ../../../wood-limit-state-basis.md
[prior-screen]: ../current-wood-splitting-method-attempt01/README.md
