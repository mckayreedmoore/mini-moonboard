# Current wood torsion method screen — attempt01

**Date:** 2026-09-27. **Status:** bounded source review; no criterion or
capacity is resolved.

This note screens the torsion methods behind `taper_sampled_rectangular_shear_torsion`,
`taper_taper_region_unbored_torsion_applicable`, and the torsion part of
`sampled_net_member`. It does not change geometry, criteria, or solver inputs.

## Finding

The published mechanics basis gives a torsional stress solution for an intact,
constant rectangular prism. A separate wood design rule can convert that
stress to a torsion resistance only when its edition, material basis, and
section applicability are selected. Neither result currently covers this
candidate's orthotropic sections at bores or cuts.

For an unbored rectangular prism with larger dimension `h`, smaller dimension
`b`, and applied torque `T`, the USDA Forest Products Laboratory Wood Handbook
gives the maximum elastic torsional shear stress as:

```text
tau_max = T / (beta * h * b^2)
```

`beta` is read from the handbook's aspect-ratio graph as a function of `b/h`.
This is a stress-recovery equation for a rectangular section. The Handbook
describes this chapter as fundamental mechanics equations and directs readers
to design standards or product sources for design procedures; the equation
does not itself establish a wood strength or allowable torque.

For the isotropic Saint-Venant prism, elastic twist per length is
`theta' = T / (G * J_t)`, where `J_t` is the rectangle's shape-dependent
torsion constant, not its polar area moment. This stiffness equation still
does not give a failure load. For timber, its shear modulus or orthotropic
material model must match the species, product, and grain frame. Davalos et al.
report that Saint-Venant's isotropic torsion solution predicts linear torsional
response for Southern Pine glulam beams and can be used to compute their shear
moduli. Their abstract separately reports transverse-isotropy support from
tests on Southern Pine solid-sawn samples and glulam beams. Those findings are
limited to the tested populations; they do not establish a general model for
all solid-sawn or glulam members. This supports an elastic stiffness and
shear-modulus method only within those experimental populations; it does not
establish a DF-L No. 2 strength criterion, a failure capacity, or validity at
bores and cuts.

## Historical EC5 candidate and edition limit

A public text copy of EN 1995-1-1:2004+A1:2008 has a torsion check in
clause 6.1.8, printed page 39 (PDF page 41):

```text
tau_tor,d <= k_shape * f_v,d

k_shape = 1.2                         (circular section)
k_shape = min(1 + 0.15 * h/b, 2.0)   (rectangular section)
```

That copy is a non-BSI-hosted text of the 2004+A1:2008 edition. This is a
historical candidate only: it does not verify the clause wording in
BS EN 1995-1-1:2004+A2:2014 or BS EN 1995-1-1:2025, and neither edition nor a
National Annex has been adopted for this analysis. Do not use this formula as
the current method until the exact adopted normative text, National Annex,
material basis, and section scope are checked. It does not authorize
substituting NDS `Fv` into a torsion equation.

In the inspected 2004+A1:2008 copy, shear and torsion appear in separate
clauses (6.1.7 and 6.1.8), followed by combined-stress provisions in 6.2. This
bounded reading does not establish the simultaneous shear-and-torsion rule
for either BSI-listed edition. That interaction remains unresolved until the
adopted full text and all applicable clauses are reviewed. The rectangular
rule also does not turn a section with bores, housings, notches, or other cuts
into a rectangular section, and it supplies no section-specific stress
concentration solution for those openings. The repo's NDS-based method screen
found no NDS torsion resistance equation for these sections. `Fv` alone is
not torsional resistance.

## Evidence route for cut sections

ASTM D198-22a is an active structural-size static-test standard with a torsion
procedure (Sections 37–44). A test program on representative finished
sections could measure torque-twist response and torsional failure for the
actual bore/cut geometry, provided the specimen and setup meet the licensed
standard's requirements. That would be test evidence, not an automatic design
allowable or a result for an untested member. ASTM D2915-25 covers sampling
and data analysis; it says statistical estimates need further adjustment for
an accepted design method and does not prescribe the action after analysis.
The test route therefore still needs a defined representative population,
service/design adjustments, and an accepted conversion to resistance. A
pure-torsion test also does not establish a combined shear/torsion criterion.

## Applicability disposition

- Keep the rectangular elastic stress solution limited to co-located,
  unbored, constant rectangular stations with a justified wood shear-modulus
  model. An unbored station check does not clear a nearby discontinuity.
- At any section crossed by a bore or cut, the full rectangular solution and
  EC5 rectangular `k_shape` rule have no demonstrated applicability here.
  Do not infer a net-section torsion resistance from area reduction alone.
- Keep torsion resistance and simultaneous shear/torsion interaction
  `UNRESOLVED_METHOD`; no current accepted torque demand or capacity is
  recorded. Existing criteria remain `pending`.

The source-bound next input is an applicability map from each critical station
to its finished section class (unbored rectangle or bore/cut), grain frame,
and simultaneous signed torsion/shear demand. For bore/cut stations, the
remaining method choice is either a source-matched full-size test program
with a design conversion or a validated orthotropic section method with a
wood-specific strength criterion. No material values or capacities are
assigned by this screen.

## Repository source snapshots

- `docs/wood-joints-mvp/wood-limit-state-basis.md` — SHA-256
  `1110e664a88f704773a463e83a2aeac3954b978048d811e4bff1effa55aa7c2e`
- `docs/wood-joints-mvp/criteria-method-map.md` — SHA-256
  `2ab30c154d75306cb83c88fdde98f7af8082b3c57089a9fdf587c5b3b9818182`
- `docs/wood-joints-mvp/criteria.json` — SHA-256
  `fd1df5f106b944d21bc237d0ff789eb30437640ce81cb3e059c7e21f3a531784`
- `docs/wood-joints-mvp/current-criteria-coverage.md` — SHA-256
  `ccda149cf7add227a7a038311625595764331c57a43af6b23de973a88d1b6e0a`
- `current-wood-resistance-method-screen-attempt01/README.md` — SHA-256
  `238afb034bb90c7945af1a6ec2c01dfeb3d9fee13c20f47340f1f8e00834d3f1`

## Sources checked 2026-09-27

- [USDA Forest Products Laboratory, Wood Handbook, Chapter 9](https://research.fs.usda.gov/treesearch/37423)
  and [chapter PDF](https://research.fs.usda.gov/download/treesearch/37423.pdf):
  Eq. 9-24 and Fig. 9-6 give the unbored rectangular stress solution; the
  chapter identifies itself as mechanics equations and points to design
  standards for design procedures.
- Davalos, Loferski, Holzer, and Yadama, [Transverse Isotropy Modeling of 3-D
  Glulam Timber Beams](https://doi.org/10.1061/(ASCE)0899-1561(1991)3:2(125)),
  *Journal of Materials in Civil Engineering* 3(2), 125–139: experimental
  torsion/stiffness support for the tested Southern Pine class.
- [BSI record for BS EN 1995-1-1:2004+A2:2014](https://knowledge.bsigroup.com/products/eurocode-5-design-of-timber-structures-general-common-rules-and-rules-for-buildings):
  edition status and scope only; no clause text was available in the inspected
  record.
- [BSI record for BS EN 1995-1-1:2025](https://knowledge.bsigroup.com/products/eurocode-5-design-of-timber-structures-general-rules-and-rules-for-buildings):
  second-generation edition status only; no clause text or National Annex is
  selected here.
- [Public text copy of EN 1995-1-1:2004+A1:2008](https://www.phd.eng.br/wp-content/uploads/2015/12/en.1995.1.1.2004.pdf):
  clauses 6.1.7, 6.1.8, and 6.2, printed pages 38–40 (PDF pages 40–42).
  The inspected PDF SHA-256 is
  `05042b33af906ef5b9c3eaace5c14258f11fa2bc69ee9cb2479d611634444c8c`.
  This non-BSI-hosted 2004+A1:2008 text is evidence only for that historical
  edition, not for either BSI-listed edition above.
- [ASTM D198-22a](https://store.astm.org/d0198-22a.html): active edition;
  structural-size static test methods include torsion in Sections 37–44.
- [ASTM D2915-25](https://store.astm.org/d2915-25.html): active sampling and
  data-analysis practice; its estimates require a further accepted design
  method and applicable adjustments.
- [AWC 2024 NDS](https://awc.org/resources/2024-nds/): repository's U.S.
  design basis; no NDS torsional capacity has been assigned in this screen.
