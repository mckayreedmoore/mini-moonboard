# Provisional floor-friction and mass assumptions

Reference checkpoint: 2026-09-11. This document supplies another reviewer with
sources and assumptions to verify. It does not change any FE input, establish
a climbing-load rating, or approve the actual floor. Climber-load criteria are
tracked separately from this floor/mass reference.

## Values to retain as explicitly provisional

| Quantity | Current numerical choice | Status and intended use |
| --- | ---: | --- |
| Floor coefficient of friction | 0.10, 0.20, 0.40 | Analyst-selected sensitivity points; no value is a manufacturer rating or verified lower bound |
| Wood and plywood density | 600 kg/m³ | Shared CAD mass assumption; not a certified property of selected DF-L or APA plywood |
| Included mass scale | 0.80 and 1.00 | Analyst-selected floor sensitivity; scales included mass at fixed center of gravity, not a statistical confidence interval |
| Steel density | 7850 kg/m³ | Conventional engineering approximation used by the existing mass model; purchased hardware mass remains simplified |

Do not select a favorable coefficient because its case passes. A contaminated,
coated, wet or moving interface may fall outside this sensitivity range. Greater
dead weight can improve sliding resistance while changing member and joint loads;
600 kg/m³ is not uniformly conservative. Holds, T-nuts, hold bolts, electrical
equipment and other omitted items also change actual mass and center of gravity.

## Primary friction evidence and transfer limits

Robbins and Riskowski measured Douglas-fir bulkheads on building floors. Their
reported mean static coefficients were 0.58 on smooth concrete and 0.81/0.86
on rough concrete for loading parallel/perpendicular to sweep marks. They
suggested maximum design values of 0.5 and 0.6 respectively and found that soil
or soybean debris reduced friction. These are that study's results, not this
frame's acceptance values. The accessible abstract does not establish matching
moisture, pressure, surface preparation or statistical lower bounds for this
installation. [ASABE, *Coefficient of Static Friction for Wood Bulkheads on
Building Floors*, 1990](https://elibrary.asabe.org/abstract.asp?aid=31569&redir=&redirType=&t=1)

Rubber pads do not provide a universal friction coefficient. Persson and
coauthors report that rubber friction on wet rough substrates at low sliding
velocities is typically 20–30% below corresponding dry conditions. Their work
concerns tire/road friction; it does not specify a static allowable coefficient
for a particular support pad or indoor floor. No rubber product or pad-to-wood
attachment is selected here, and no increased coefficient is credited.
[Persson et al., *Rubber friction on wet and dry road surfaces*, 2005](https://arxiv.org/abs/cond-mat/0502495)

## Density reference and verification

The USDA wood-property reference lists Coast Douglas-fir at approximately
34 lb/ft³ under its 12% moisture-content table, about 545 kg/m³ after unit
conversion. That species-average clear-wood reference is neither a measured
No. 2 board density nor a plywood specification. The selected DF-L grade may
contain a species mix, and panel veneers, adhesive and moisture affect plywood
mass. Keep 600 kg/m³ labeled as an analyst choice until actual stock is weighed.
[USDA Forest Products Laboratory, *Wood*, Table 6.7.2](https://www.fpl.fs.usda.gov/documnts/pdf2007/fpl_2007_green001.pdf)

## Reviewer handoff

1. Identify the actual substrate and finish beneath every foot, including any
   pad and its separate wood/pad interface. Record expected moisture and debris.
2. Establish a defensible lower-bound friction input for those interfaces and
   relevant normal pressures. A single peak pull measurement is not a guaranteed
   coefficient; record repeats, direction and transition to sliding.
3. Weigh representative delivered lumber and plywood with measured dimensions
   and moisture, then reconcile complete assembly mass and center of gravity.
4. Reassess floor equilibrium and compliant support behavior with those inputs.
   Existing rigid-floor feasibility does not establish stiffness, local pressure,
   rocking, transient motion or connection resistance.

Until those checks are complete, report conditional results at each assumed
coefficient and mass scale. Do not convert them into an unconditional user-weight
rating or claim that adding rubber makes the design pass.
