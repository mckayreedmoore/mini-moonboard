# Centered passage: dimensional acceptance and bending reference

**The nominal centered hole has no fabrication tolerance margin. The bending material reference is now independently verified; member resistance remains open.** This calculation applies only to the isolated 38.1 mm transverse passage in 38.1 × 139.7 mm stock in `round-structural-development`. It consumes no historical numerical demands. This is an isolated nominal-dimension calculation, with no current CAD geometry-match gate; the candidate label does not authenticate model geometry.

The reproducible [calculation](../fea/round_structural_timber_reference.py) produces [these results](../fea/results/round-structural-timber-reference.json). Run `.venv/bin/python -m fea.round_structural_timber_reference --output fea/results/round-structural-timber-reference.json`. The output records the calculator source hash and the downloaded primary PDF hash. The CLI refuses to overwrite existing evidence; use a new output filename to reproduce a later run. The five focused tests verify tolerance rejection, invalid-input rejection and independent two-ligament section arithmetic.

## A finite dimensional acceptance rule

ICC's [CodeNotes](https://www.iccsafe.org/building-safety-journal/bsj-technical/codenotes-cutting-drilling-and-notching/) illustrates the sawn-member hole limits. Using its two-inch edge comparison as the proposed local-detail basis, require both actual front and rear clearances to be at least 50.8 mm. For actual stock depth `d`, maximum actual bore diameter `D`, and maximum error `e` from the center of the **actual measured depth**, this means:

`d >= D + 101.6 + 2e`, with `D <= d/3`.

This expresses an inspectable dimensional acceptance rule; it does not authorize adopting a floor-framing provision for every load and connection in this equipment.

| Dimensional scenario | Minimum edge clearance | Edge comparison |
|---|---:|---|
| Exact 139.7 mm depth, exact 38.1 mm bore, exact centering | 50.8 mm | Meets with zero margin |
| Depth 0.5 mm below nominal, bore 0.5 mm oversize, center error 0.5 mm | 49.8 mm | Fails by 1.0 mm |
| Actual depth 141.2 mm, bore 38.6 mm, center error 0.5 mm | 50.8 mm | Meets with zero remaining margin |

Any positive shortfall, oversize or centering error defeats the exact nominal edge comparison if other dimensions remain nominal. The 141.2 mm example is a required **actual** depth, not an instruction to substitute stock or alter CAD. With a further 0.5 mm shortfall allowance, the specified nominal depth would need to be at least 141.7 mm. The present nominal 2x6 model stays intact; a release must either select and inspect material/drilling against the actual rule or accept a separately justified local-opening detail. The rule still needs the complete other-hole/notch and connection-region checks described in the [timber review](round-structural-timber-review.md).

## Independently verified bending reference

The accessible primary [AWC 2024 Design Values for Joists and Rafters](https://web-media.awc.org/wp-content/uploads/2023/11/17210143/AWC_DVJR2024_20231130_AWCWebsite.pdf#page=9), Table W-1, printed page 5, gives US Douglas Fir-Larch No.2 nominal 2x6 normal-duration bending of 1,345 psi including repetitive-member use. Its table instruction reduces bending by 13% for wider spacing. Applying that reduction and rounding down gives **1,170 psi**. This independently corroborates the previously recorded `900 × 1.3` bending reference without relying on an inaccessible Supplement download. It does not independently verify the remaining Supplement values for tension, shear, compression parallel to grain or minimum modulus.

Use that bending reference only for matching grade/species, dry unincised stock, ordinary temperature and normal duration. It contains no impact-duration, flat-use or repetitive-member increase. Beam stability and the acceptability of the hole detail remain separate conditions; this reference does not establish either.

At the center of a transverse hole, the removed section is a full-width rectangular strip. With centered diameter `D`, width `b` and depth `d`, the two remaining ligaments give `A = b(d−D)`, `Istrong = b(d³−D³)/12`, and `Iweak = (d−D)b³/12`.

| Isolated section quantity | Result |
|---|---:|
| Net area | 3,870.96 mm² |
| Strong-axis section modulus | 121,413.247 mm³ |
| Weak-axis section modulus | 24,580.596 mm³ |
| Strong bending reference × section modulus | 979.424 N·m |
| Weak bending reference × section modulus | 198.288 N·m |

These are conditional arithmetic products, not allowable moments for the frame. They exclude the reduction needed for unverified restraint and local opening behavior. A member with simultaneous axial force, biaxial bending, shear or torsion requires its actual combined-load calculation; separately comparing each moment with a product does not establish that interaction. Connections and additional holes can govern before this isolated section does.

## Interface to the current load calculation

Provide each cut's simultaneous `N, Vstrong, Vweak, Mstrong, Mweak, T`, signed and expressed at the section centroid, in N and N·mm. The centered gross and net centroids coincide at `N = 69.85 mm`; retain actual connection eccentricities when deriving the moments. Strong bending is about X for a principal and about local S for a horizontal rail. Provide both effective column lengths, lateral/torsional restraint and the proposed accepted local-detail basis with the demand record. The independently acting panels cannot automatically supply bracing or equal load distribution. Recover end-bearing and concentrated connection zones separately; the center-of-hole section excludes them.

The current-frame free body must determine those demands. The former continuous rear-prism diagnostic remains a different stiffness model and supplies no conservative force bound for this calculation. The remaining member review is therefore finite: current actions, accepted restraint, actual material and dimensional acceptance, combined-load/stability checks, and the affected connection/bearing regions. This calculation resolves the dimensional rule and bending reference only.
