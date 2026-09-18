# Provisional connection assumptions for independent review

Checked September 11, 2026. This is a review ledger, not construction approval.
The current horizontal-service candidate retains 87 SPAX panel/kicker screws,
manufacturer SDS bracket screws and 3/8-inch through-bolts. Inserts remain a
separate development option. Nothing below changes the CAD, native input decks,
published source identities or installed hardware schedule.

## Published stiffness models and proposed interpretation

The current 100, 1,000 and 10,000 N/mm connector sweep is an **assumed sensitivity
study**, not a published load-slip calibration. Equal stiffness in global X/Y/Z
does not distinguish withdrawal, lateral embedment, screw stretch, washer
bearing, bracket deformation or bolt-hole clearance.

[Swedish Wood, Design of Timber Structures Volume 2, third edition 2022,
section 9.2, Table 9.2, printed page 33](https://www.swedishwood.com/siteassets/5-publikationer/pdfer/sw-design-of-timber-structures-vol2-2022.pdf)
summarizes EN 1995-1-1:2004 Table 7.1:

`Kser = rho_mean^1.5 * d / 23 [N/mm]`

This is serviceability **lateral slip**, per fastener and shear plane, for its
listed dowels, bolts, screws and predrilled nails. Density is mean kg/m³ and
diameter is mm; dissimilar wood densities use their geometric mean. Bolt-hole
clearance contributes additional slip. The handbook is educational, not the
governing standard for this US project. Its steel-to-wood multiplier cannot
represent an entire flexible angle assembly.

Illustrative calculation at assumed 500 kg/m³: diameters 4.1402/9.525/6.5024 mm
give 2,013/4,630/3,161 N/mm before any steel-interface factor. These are not
selected properties. Neither CAD mass density nor NDS specific gravity establishes
the required mean density; check fastener and drilling applicability separately.

[Volume 1, section 4.16, equations 4.34–4.35, printed page 114](https://www.swedishwood.com/siteassets/5-publikationer/pdfer/sw-design-of-timber-structures-vol1-2022.pdf)
gives the associated older-Eurocode `Ku = (2/3) Kser` ultimate-state stiffness
approximation. It is not an ultimate load, resistance factor or assertion that
the connection remains linear to failure. The [JRC 2025 Eurocode workshop,
connection-design slides](https://eurocodes.jrc.ec.europa.eu/sites/default/files/2025-08/250603-JRC_Eurocode_5_Dietsch_Frangi_Schenk_website.pdf)
also distinguishes service and ultimate slip slopes and initial clearance.

For an explicitly **borrowed axial analogy**, [Rotho Blaas ETA-11/0030,
issued August 20, 2025](https://www.rothoblaas.com/attachments/271032-product-756/ETA_11_0030_RB_screws_2025.pdf)
provides `Kser = 25*d*l_eff N/mm` for the threaded portion of its softwood
fasteners. Using 4.1402 mm and 31.496 mm merely illustrates 3,260 N/mm.
This is not a SPAX calibration. Complete panel retention also involves head
bearing and screw deformation; components acting in series lower assembly
stiffness. Do not apply the axial formula to lateral directions, whole brackets,
machine screws in zinc inserts, or compression contact.

**Next-model assumption proposal:** replace the universal isotropic spring only
in a new diagnostic with separately named lateral and withdrawal stiffnesses,
an explicit initial bolt-clearance model, and independent compression contact.
Keep the existing sweep as historical evidence. Review applicability and density
first; these sources do not establish universal upper and lower stiffness bounds.

## SPAX panel/kicker strength references

[DrJ TER 2010-02, November 4, 2025, Tables 2/6/10](https://www.drjcertification.org/report/download/1936):
XFT08P-2000 #8×2-inch flat-head: 1.240-inch thread including tip;
DF-L SG0.50 face-grain withdrawal **133 lbf/in**; 23/32-inch plywood SG≥0.50
head pull-through **212 lbf**; steel-only allowable tension/shear **460/345 lbf**.
Withdrawal requires ≥1-inch embedded thread including tip. Apply NDS adjustments
and installation conditions. Lumber SG does not establish plywood SG; no DF-L
lateral connection value is assigned here.

Our conversion uses 4.448221615 N/lbf: optimistic full-thread withdrawal is
**733.60 N**, conditional head reference **943.02 N**, steel tension/shear
**2,046.18/1,534.64 N**. Grooves, combined action and splitting remain unresolved.

## What the completed native probes show

The [saved signed-demand screen](../fea/results/horizontal-panel-fastener-screen-v1.json)
contains 696 connector results from the eight coupled cases. The
[diagnostic archive instructions](horizontal-frame-diagnostic.md) provide the
underlying solver evidence.

Run the signed extraction without a solver:

```sh
uv run python -m fea.horizontal_panel_fastener_screen \
  --directory fea/generated/horizontal-frame-batch-v2 \
  --output /tmp/new-panel-fastener-demand.json
```

The script authenticates batch reports and their source snapshots, matches
current geometry and all 87 connector identities, and records changed solver
or exporter sources separately. It uses eight coupled cases; the two
framing-load controls are excluded. First spring endpoint is wood, so
`T = max(0, -F_first dot screw_direction)` is withdrawal tension. Positive axial
force is compression. Lateral demand is the orthogonal vector magnitude.

| Probe and connection | Withdrawal tension | Lateral force | T / optimistic withdrawal reference | T / conditional plywood-head reference |
| --- | ---: | ---: | ---: | ---: |
| F10, k=1,000; `timber_panel_upper_left_8` | 1,064.39 N | 317.30 N | 1.451 | 1.129 |
| C6, k=1,000; `horizontal_panel_lower_left_3` | 961.65 N | 55.13 N | 1.311 | 1.020 |
| C10, k=10,000; `timber_panel_upper_left_1` | 0 N; 163.16 N compression | 1,495.29 N | 0 | 0 |

Thus the existing #8 choice **exceeds the unadjusted axial references** in two
250 lb probes. This is a concrete reason to investigate panel retention.
It is not proof of adjusted-capacity or physical failure: applicable duration
and other factors, actual plywood, connection stiffness and combined resistance
remain unresolved. Conversely, numerical convergence is not a strength pass.
Maxima over these finite probes are not a guaranteed bound on slip or loading.

## Unselected larger washer-head candidate

Same TER, Tables 4/6/10: **XWT10-2500**, #10×2½-inch under-head length;
major/head diameter **0.200/0.470 inch**, head height **0.085 inch**, thread
**1.500 inch**; DF-L withdrawal **176 lbf/in**, specified plywood head **322 lbf**.
Full embedment gives **1,174.33/1,432.33 N** respectively.

**Not selected; fit unchecked.** Our panel geometry requires 45.24375 mm receiver
reach, beyond the 17 mm insert reservation. The head protrudes. Check grooves,
tip cover, neighbors, installation and supply before changing CAD. Recessing
would invalidate this unrecessed-head comparison. Larger separate references
do not qualify combined demand. Keep bracket SDS and insert development separate.

## ML24Z and SDS25112 references

[Simpson L-C-MLZ25, December 23, 2025, page 1 table](https://ssttoolbox.widen.net/content/iczmiabsx6/pdf/L-C-MLZ25.pdf)
gives single/end ML24Z DF/SP allowable loads F1/F2/F3/F4 of
595/450/450/750 lbf (2,646.69/2,001.70/2,001.70/3,336.17 N), using all six
SDS25112 screws. Its bearing installation has no F2 value. These ML24Z loads
do not receive a duration increase. Map the actual loaded member and Figure
directions separately for every angle; do not sum screws, divide bracket
capacity into six independent values, or invent a combined-axis interaction.
The letter does not provide an assembly stiffness curve. Cross-grain bending
and tension reinforcement remain design questions.

[ICC-ES ESR-2236, January 2026](https://icc-es.org/wp-content/uploads/report-directory/ESR-2236.pdf),
Table 1, lists SDS25112 1½-inch length, one-inch thread, 0.188-inch root,
and carbon-steel bending yield 172,000 psi. Steel-only ASD tension/shear are
1,430/800 lbf (6,360.96/3,558.58 N); they are not wood-joint capacities.
Table 5 gives face-grain withdrawal 172 lbf/in for assigned SG≥0.50 with at
least one inch embedded thread, including tip, and required NDS adjustments.
Generic SDS edge/end/spacing conditions remain distinct from evaluated
connector applications. No independent SDS stiffness is selected here.

Downloaded primary identities for reproducibility (vendor files not committed):

```text
L-C-MLZ25.pdf SHA256 88d9051a9eadc08508a1a1c591914217309d6a2c1a281b375149d0cc57e584ff
ESR-2236.pdf SHA256 fa4c7b7787c8690a10952bbd1dd7227ebba5ea422fd179f1b74c7c87443ab519
```

## Through-bolts and inserts

[AWC TR12, Table 1-1](https://awc.org/wp-content/uploads/2021/12/AWC-TR12-1510.pdf)
provides dowel yield equations, not a universal 3/8-inch bolt rating or slip law.
The existing `fea.lumber_leg_resistance.bolt_reference()` returns **668.03 N**
for two 38.1 mm solid sawn members, 0.298-inch effective diameter, 3,650 psi
bearing inputs and assumed 45,000 psi bending yield with its stated reduction
terms. This conditional single-shear calculation must not be transferred to
the plywood gussets, different bearing directions, axial washer action or bolt
groups. Purchased steel/thread properties, gaps and net sections remain open.

E-Z LOK 801420-13 plus Dottie FMDD14114 remains geometry development only.
[E-Z LOK's testing policy](https://www.ezlok.com/testing) does not supply Hex
Drive mechanical test results because installation variables affect behavior.
The 12.1412×17 mm reservation is a fit hypothesis, not a withdrawal or cyclic
rating. No published insert-system stiffness or applicable allowable was found;
do not borrow the screw, bolt or Rothoblaas numbers for it.

## Questions for the independent reviewer

1. Confirm applicable US load combinations, load duration and repeated climbing
   action; identify an appropriate comparison between the diagnostic forces and
   adjusted connection resistance.
2. Verify actual plywood assigned SG, product layup and local head/hold behavior;
   select the effective screw embedment around every groove.
3. Decide whether older-Eurocode lateral slip and the separate proprietary axial
   analogy are acceptable sensitivity inputs; specify material density,
   fastener diameter, clearances, nonlinear behavior and direction mapping.
4. Derive each angle's resultant and local moment demand from its six screw
   stations before applying directional assembly references.
5. Complete applicable lateral/axial interaction, splitting, group action,
   washer bearing, member net sections and whole-frame stability. Preserve
   all unqualified flags until those checks actually close.
