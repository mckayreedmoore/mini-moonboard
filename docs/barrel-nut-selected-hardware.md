# Direct cross-dowel selected qualification hardware

This records the hardware selected for the next bounded qualification step of
`compact-floor-flush-bolted-development`. It is not a shopping list,
fabrication release, structural approval, or change to the selected angle-frame
candidate. The machine-readable selection is
[`barrel-nut-selected-hardware.json`](barrel-nut-selected-hardware.json).

## Decision

The direct cross-dowel design does **not** currently work as a validated DIY
design. Its disposition is **EVIDENCE_BLOCKED**. The current twelve 1/4-20 ×
6-inch outer-rail bolts fail closed and are rejected for this selection: their
adverse complete-thread endpoint does not reach the modeled barrel axis. That
does not prove physical joint failure because required effective engagement is
still unknown. Replacing them with controlled 6.5-inch bolts is a feasible
geometry correction, not a strength pass.

The selected qualification stack is:

| Use | Selected article | Quantity | Controlled basis | Disposition |
| --- | --- | ---: | --- | --- |
| Cross-dowel barrel | STAFAST `JCD14201606NL ZN`, 1/4-20, nominal 0.394 × 0.630 inch | 48 | Manufacturer nominal geometry only | Test article; not structurally qualified |
| 3.5-inch bolt | CDE `1456BHT5`, fully threaded Grade 5 | 8 | SAE J429 / ASME B18.2.1 / IFI-199 | Pending manufacturer certificate and Class 2A confirmation |
| 4.5-inch bolt | CDE `1472BHT5`, fully threaded Grade 5 | 24 | SAE J429 / ASME B18.2.1 / IFI-199 | Pending manufacturer certificate and Class 2A confirmation |
| 5-inch bolt | CDE `1480BHT5`, fully threaded Grade 5 | 4 | SAE J429 / ASME B18.2.1 / IFI-199 | Pending manufacturer certificate, Class 2A confirmation, and deeper blind bore |
| Outer-rail bolt | CDE `14104BHT5`, fully threaded Grade 5, 6.5 inch | 12 | SAE J429 / ASME B18.2.1 / IFI-199 | Pending manufacturer certificate and Class 2A confirmation |
| Washer | Fastenal `33857`, hardened 1/4-inch USS/Type A wide | 48 | ASTM F436/F436M / ASME B18.21.1 | Pending lot MTR and finished-seat fit |

For a 1/4-20 tensile stress area of 0.0318 in², the selected Grade 5 bolt basis
gives constituent minima of 2,703 lbf proof, 2,926 lbf yield, and 3,816 lbf
ultimate tension. These values qualify neither the barrel nor the timber
joint. The selected washer's adverse annular steel area is 213.63 mm² before
seat eccentricity or loss of sound wood support.

## Public online evidence audit

Checked 22 September 2026. Public manufacturer evidence closes only part of
the hardware-input gate:

| Item | Public evidence found | What remains unavailable online | Result |
| --- | --- | --- | --- |
| STAFAST `JCD14201606NL ZN` | The [manufacturer product page](https://shop.stafast.com/jcd14201606) gives 1/4-20, `d1 = 0.394 in`, `L = 0.630 in`, `L1 = 0.236 in`, and steel. The [manufacturer catalog](https://shop.stafast.com/catalogdownloads/downloads.aspx) gives a generic ±0.016-inch decimal tolerance and “quality cold rolled steel.” | Current controlled print, thread class, complete usable female-thread interval, material minimums, proof/strip/wall resistance, and lot conformity. The catalog says functional specifications can change and directs users to request a current print. | **Public catalog data supports sensitivity only; exact manufacturer print plus lot evidence or complete-joint lot testing is required.** |
| CDE Grade 5 tap bolts | The [manufacturer dimensional sheet](https://cdefasteners.com/sites/default/files/product-specs/capscrewtapbolts.pdf) and product family identify fully threaded Grade 5 bolts governed by SAE J429, ASME B18.2.1, and IFI-199. CDE states that manufacturer certificates are available. | Certificate and Class 2A confirmation tied to the delivered `1456BHT5`, `1472BHT5`, `1480BHT5`, and `14104BHT5` lots. | **Public standard basis available; delivered-lot evidence must be obtained with the order.** |
| Fastenal `33857` washer | Fastenal's [controlled product standard](https://www.fastenal.com/content/product_specifications/FW.HRD.USS.A.Z.02.pdf) gives the 1/4-inch ID, OD, and thickness limits and invokes ASME B18.21.1, ASTM F436/F436M, and lot-traceable MTR requirements. | MTR and dimensions for the delivered lot; finished-seat and tool fit. | **Controlled product standard available; delivered-lot and installed-fit evidence remains required.** |
| Controlled structural barrel comparator | Howmet publishes an [F1800-4 product record](https://catalog.howmetfasteners.com/item/other-products/f1800-barrel-nut-floating/f1800-4) and [controlled drawing](https://catalog.howmetfasteners.com/Asset/s_F1800-%28%29_C.PDF) with material, tolerances, and a 7,200 lbf minimum axial tensile value. | Applicability to this joint. It is a floating 1/4-28 aerospace nut requiring a 13.487–13.589 mm installation bore, not the selected direct 1/4-20 cross dowel; its metal rating does not qualify wood. | **Data available, but only for an incompatible redesign comparator.** |
| Complete DF-L cross-dowel joint | Public timber literature establishes that crossed-bore failures and stiffness depend on wood, bore fit, geometry, loading, and confinement. | No source covers this 10 × 16 mm barrel, current crossed cuts, two-row principal/header geometry, reversed signed twist, delivered DF-L, or complete retained panel/bolt load path. | **Not available; representative adverse-specimen testing remains required.** |

Therefore online research cannot turn this selection into a structural pass.
It can freeze bolt and washer procurement requirements and show what controlled
barrel evidence would look like. It cannot supply the selected barrel's
missing resistance or the complete timber joint's strength and stiffness.

## Why this barrel was selected

[STAFAST `JCD14201606NL ZN`](https://shop.stafast.com/jcd14201606)
is the closest manufacturer-identified article to the existing 10.0076 ×
16.002 mm CAD body and retains 1/4-20 bolts. Its thread axis is 5.9944 mm from
the slotted end, not the modeled centered 8.001 mm. Preserving the bolt axis
therefore requires a declared insertion orientation and a 2.0066 mm barrel-body
shift, followed by the recorded combined-cut and access checks.

A source-built nominal check applied that shift to all 46 bodies in the prior
topology's full 20-timber/268-cutter assembly. The vertical-center proposal
inherits 44 unchanged pairs, removes two angled principal pairs, and separately
checks four new vertical pairs, for 48 proposed pairs. Every shifted body and added 2.0066 mm
bore tail stayed inside its intended receiver; none intersected unrelated
wood, another cutter, or protected hardware. Shifted insertion depths range
from 29.058 to 70.508 mm. This closes nominal placement only. Unpublished part
and finished-bore tolerances still prevent a fit or remaining-wood pass.

No public controlled STAFAST evidence fixes its current tolerances, thread class,
complete female-thread interval, material minimum, proof/strip load, barrel
wall resistance, or lot conformity. It is selected only because it is the
shortest geometry-compatible article for a lot-specific hardware and complete
wood-joint test program. It may not be silently replaced by Hillman or RAMPA.

The fully documented aerospace alternatives do not shorten this path.
SPS `2452-048` and Shur-Lok `SL414-4` use 1/4-28 hardware and different barrel
cuts. Their published axial tests use high-strength bolts in close-fitting
hardened/alloy-steel fixtures. Those results demonstrate metal hardware
capability, not barrel retention, splitting, pocket survival, or stiffness in
wood. The larger Shur-Lok cuts also reduce the current principal-member barrel
ligament. They remain redesign comparisons, not selections.

## Fit and geometry result

The CDE `1496BHT5` 6-inch controlled comparator is rejected for all twelve
outer-rail rows. In
the adverse standard-length/selected-thick-washer stack, its physical tip ends
1.072 mm short of the modeled barrel axis. After a conservative two-pitch tip
allowance, the complete-thread endpoint is 3.612 mm short. This rejects the
part selection; it does not establish a joint failure load.

The selected CDE 6.5-inch bolt covers the full modeled 10.0076 mm barrel body
in the same axial screen. With the selected washer and the CDE greater-than-
6-inch length tolerance, it needs 10.4408 mm more blind-bore depth merely to
avoid bottoming. A provisional 2 mm tip reserve requires 12.4408 mm. The prior
11.069 mm source-built probe stayed inside each intended rail but used the
wrong length-tolerance band and omitted the selected washer shift; it leaves
only about 0.628 mm adverse clearance and is superseded. A corrected
source-built 12.4408 mm probe keeps all twelve bores wholly inside their
receivers with no unrelated-wood, protected-feature, peer-barrel/path/stack,
or maximum-washer collision. Final bore depth remains open until the lot
dimensions, female thread exit, drilling tolerance, and required tip clearance
are frozen; the 2 mm reserve is still provisional.

The selected 5-inch adverse stack retains only 0.1204 mm nominal clearance
before any machining error, so it also needs a controlled deeper blind bore.
The 3.5- and 4.5-inch families remain geometry candidates. Every family still
depends on the barrel's measured usable female-thread interval and a supported
required engagement.

The selected washer is 18.4658–19.0246 mm OD and 1.2954–2.0320 mm thick. The
current 19.05 mm nominal seats provide essentially no diametral machining
allowance, and the current CAD under-models the maximum head-plus-washer stack
by 0.807 mm. Finished seats and tools must be screened with delivered parts.

## Current metal threshold screen

Using the conservative 301.494 N old-topology service proxy rather than the
220.476 N redistributed contact witness, a controlled whole-barrel design
rating must exceed:

```text
installation preload + gamma × 301.494 N
```

With the publicly posted 2016 catalog's provisional adverse 0.378-inch body
diameter and a two-pitch complete-thread deduction, NASA RP-1228's tapped-hole
expression
requires female-thread shear strength of `7.380 × gamma MPa`. A provisional
barrel-lobe sensitivity requires `18.579 × gamma MPa` average shear and
`96.126 × gamma × Kt MPa` yield. These are requirement thresholds, not
STAFAST properties or accepted wall/flexure methods. `gamma`, installation
preload, `Kt`, slot geometry, thread-flank distribution, and controlled
material minima remain unfrozen. A supplier-controlled whole-component design
allowable is the shortest no-test evidence route.

The executable sensitivity is
[`scripts/owner_barrel_metal_threshold.py`](../scripts/owner_barrel_metal_threshold.py).

## Why there is no positive design verdict yet

A standard-controlled bolt and washer close only constituent steel inputs.
No accepted calculation found in the current evidence maps the direct axial
bolt load, orthogonal barrel thread, crossed wood bore, remaining ligaments,
and reversed twist into a complete timber-joint resistance. The NDS ordinary
lateral-dowel equations do not represent that load path. NASA-STD-5020B also
requires controlled nut/insert allowables or dedicated testing and treats
pullout from nonmetallic parent material as test-derived.

The revised principal/header proposal has two vertical bolts per principal and
flat underside header seats, so the former one-bolt free rotation and 2.092 mm
angled head-pocket stock no longer apply. Exact face cells now provide a static
`My` equilibrium witness for both proxy signs. Corrected actual-face rays also
show both barrel centers only 36.551 mm from the adverse grain end, reducing the
smaller adapted bearing reference to 346 N. Nominal two-plane and splitting
surfaces are mapped, but adverse tolerances, group tear-out, adopted splitting
resistance, compatible stiffness, and fresh candidate demands remain open.

## Exact closure sequence

1. Obtain the CDE certificates and the Fastenal washer MTR. Measure every
   selected barrel and map it to a station; gauge the complete female thread
   from both sides.
2. Freeze a finished-bore process from actual offcuts and delivered hardware.
   Record minimum/maximum clearance, axis error, insertion force, orientation,
   removal, damage, and moisture state.
3. Apply those measured bounds to all combined-cut solids, the 2.0066 mm
   STAFAST shift, the 5-inch bore correction, and the twelve 6.5-inch bore
   corrections. Any breakout, invalid solid, collision, or nonpositive fit is
   `NO_GO`.
4. Run the existing exploratory response stage on actual minimum-section
   joints to bound clearance, seating, stiffness, opening, twist, reversal,
   residual set, and reassembly. It supplies no strength credit.
5. Run the six fresh signed cases only after those stiffness bounds exist. The
   two-bolt/contact topology can close all six equilibrium components in the
   old proxies, but fresh demand and compatible force sharing must still pass.
6. Freeze demand-derived acceptance loads and execute the prospective
   complete-joint qualification plan. Include actual barrel lot, adverse bore
   fit, minimum wood sections, pocket/service cuts, both signs, retained bolts,
   and panel load paths. A single successful pilot can reject a bad design but
   cannot qualify it.
7. Separately demonstrate delivered-tool installation and disassembly access,
   and measure plywood capable of the fixed six-part kerf-right nesting.

Until all seven steps close, the barrel candidate remains unreleased and the
existing angle-frame packet remains the selected conditional DIY documentation.

## Measurement evaluator

Generate the exact 48-pair vertical-center input template with:

```bash
.venv/bin/python scripts/owner_barrel_selected_hardware.py --measurement-template
```

After filling it from the receiving checklist, evaluate it with
`--measurements PATH`. Each pair checks complete male/female thread overlap,
tip-to-bore-cap clearance, minimum and maximum insertion clearance, and
measured axis-offset margin. Missing actual values or acceptance limits return
`EVIDENCE_BLOCKED`; a violated supplied limit returns `NO_GO_MEASURED_FIT`.
Even all 48 passing returns only `PASS_GEOMETRY_ONLY`, never structural or DIY
release.
