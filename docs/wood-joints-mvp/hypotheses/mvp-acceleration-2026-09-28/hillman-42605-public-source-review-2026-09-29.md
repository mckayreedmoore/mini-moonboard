# Hillman 42605 public-source review — 2026-09-29

## Engineering result and stop condition

The targeted public-source search found no manufacturer or recognized
product-evaluation document for the exact Hillman/Fas-n-Tite 42605 (#10 ×
2-1/2 in) that supplies structural connection values or product dimensions.
This records the result of the sources checked; it does not prove that no
additional manufacturer data exists. Stop the capacity screen here unless
exact-SKU evidence becomes available. Do not borrow values from other Hillman
families, infer product conformity, or treat retailer metadata as engineering
data.

The search therefore yields **no adopted withdrawal or lateral resistance,
axial load-slip stiffness, thread/root/head dimensions, steel properties,
B18.6.1 conformity, or NDS §12.1.8 allowance**. The existing conditional NDS
arithmetic in [the withdrawal preflight](panel-withdrawal-preflight.md) remains
an illustrative scale only; this search does not make that method applicable
to 42605.

## Sources checked

- The exact-SKU retailer listing identifies model 42605 as a #10 × 2-1/2 in
  wood-to-wood screw and lists consumer product characteristics, but supplies
  no structural design values or load-slip data:
  [Lowe's model 42605 page](https://www.lowes.com/pd/Hillman-10-x-2-1-2-in-Ceramic-Deck-Screws-50-Count/999995042).
- An exact-MPN retailer page describes 42605 as a bugle-head screw and lists a
  0.355 in head diameter:
  [Tractor Supply model 42605 page](https://www.tractorsupply.com/tsc/product/hillman-fas-n-tite-exterior-coated-wood-screws-%28-10-x-2-1-2%29-50-pack-1549417).
  Lowe's describes the same model as flat head. These are conflicting retailer
  labels, not verified product dimensions; neither is adopted for the head or
  countersink check. Confirm head geometry from an applicable manufacturer
  source or direct observation when that evidence is in scope.
- [ASME B18.6.1](https://www.asme.org/codes-standards/find-codes-standards/b18-6-1-wood-screws)
  describes general and dimensional requirements for wood screws. No source
  found in this search establishes 42605 conformity to that standard.
- The current [ICC-ES ESL-1284](https://cdn-v2.icc-es.org/wp-content/uploads/report-directory/ESL-1284.pdf)
  names Power-Pro, Deckplus, and Profast product families and reports coating
  corrosion performance. It does not name Fas-n-Tite 42605 or provide its
  structural connection ratings.
- [ASTM D1761](https://store.astm.org/standards/d1761) is a test-method source
  for fastener withdrawal and lateral resistance; it does not provide test
  results or stiffness for 42605.

## Gate effect

The gravity-inclusive panel-group screen still establishes a conditional
necessary total axial tension of 1.304–1.764 kN for five cases and no
individual screw share. This source search supplies no resistance against
which to compare that demand. The `a1-rear` group bound remains unresolved
because an opposing-normal kicker contact may carry load. The receiver-to-frame
path, applicable head/panel limit, installed penetration, and sharing basis
also remain open. Missing data is not a physical failure finding.

No geometry, hardware instruction, load case, solver input, or model result
was changed. No native solver was run.
