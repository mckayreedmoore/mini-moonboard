# Ordinary 1/4-in through-bolt evidence screen

Status: **retail leads and conditional NDS inputs only; no selected stack or drilling release.**
This screen follows the conditional four-bolt cleat geometry. All listed
hardware is ordinary store inventory, but the exact proposed joint stack,
thread placement, and strength are not established by these listings.

| Store lead | Published identifier | Remaining product-specific evidence |
| --- | --- | --- |
| [Home Depot Prime-Line 1/4-20 × 8 in](https://www.homedepot.com/p/310465152) | 9058821; A307 Grade A, UNC-2A | Delivered root range and thread/shank placement are not verified. The NDS bolt-class Fyb input below is conditional, not a lot test. |
| [Home Depot Prime-Line 1/4-20 × 5 in](https://www.homedepot.com/p/310326760) | 9058745; A307 Grade A, 25-pack | Thread class, delivered root range, thread/shank placement, and nut/washer stack are not verified. |
| [Home Depot Everbilt 1/4-20 × 8 in](https://www.homedepot.com/p/204281626) | 800696; A307, listed 6-in thread | Controlled root and bending-yield data absent; thread transition through wood unknown. |
| [Home Depot Everbilt 1/4-20 × 5 in](https://www.homedepot.com/p/204633308) | 800676; A307, fully threaded | Controlled root and bending-yield data absent. |
| [Lowe's Hillman 1/4-20 × 5 in](https://www.lowes.com/pd/Hillman-1-4-in-x-5-in-Zinc-Plated-Coarse-Thread-Hex-Bolt/1000379721) | 190059; partially threaded | Thread length, root range, and bending-yield data absent. The listing's A2 field is not a demonstrated joint-strength specification. |
| [Home Depot Prime-Line 1/4-20 × 1¾ in Grade 8](https://www.homedepot.com/p/310509971) | 9104706; listing states SAE J429 and ASME B1.1 | Its specified grade has a defensible yield-strength route, but the bolt is far too short for either 3¾-in or 7-in wood grip before stack hardware. It is **not** a joint candidate. |

Ordinary companion items include [Everbilt 1/4-20 hex nuts](https://www.homedepot.com/p/204274089)
and [Hillman 1/4-in washers](https://www.lowes.com/pd/Hillman-1-4-in-Zinc-plated-Standard-Flat-Washer-16-Count/3035987).
The latter listing gives 5/8-in outside diameter and 1/16-in thickness;
neither item supplies a complete rated bolt/nut/washer assembly.

## Strongest same-maker retail length lead and washer pattern

The [Prime-Line 9058745 5-in 25-pack](https://www.homedepot.com/p/310326760)
and [9058821 8-in 10-pack](https://www.homedepot.com/p/310465152)
are online-listed Home Depot A307 Grade A bolts. This is a cleaner
same-maker material lead than combining differently described singles;
local shelf stock remains unverified. A [bolt-maker's explanation of
ASME B18.2.1](https://www.portlandbolt.com/technical/faqs/bolt-thread-lengths/)
gives nominal thread lengths of `2D + 1/4 in` through 6-in length and
`2D + 1/2 in` above 6 in: **0.75 in** for the 5-in bolt and **1.0 in**
for the 8-in bolt at `D=0.25 in`. This is a standard-pattern inference,
not an exact thread-transition drawing for either delivered SKU. A
permitted runout or gaging variation and reduced-body construction could
change the effective bearing geometry. Verify both bolts' full-body
diameter and first complete thread on receipt before giving shank credit.

The modeled rail and upright wood-only grips are **3.75 and 7.00 in**.
With one 0.065-in washer under the head, the corresponding wood spans
0.065–3.815 and 0.065–7.065 in from the bolt head. Under nominal
standard threads starting 4.25 and 7.00 in from the head, the rail wood
has no thread and only the distal 0.065 in of upright wood does. Even a
**hypothetical** 0.25-in transition allowance shifts those starts to
4.00 and 6.75 in, leaving 0 and 0.315 in of thread in wood. The latter
is below a quarter of the upright-side 5.5-in cleat thickness, but this
does **not** establish the 2024 NDS full-body allowance: actual delivered
body, thread location, member assignment, seating, nut engagement and
washer stack remain to be checked. The separate
[root-only yield screen](simple-pb01-quarter-yield-screen.md) makes no
full-body claim.

Home Depot also online-lists [Everbilt 807210 wide flat washers](https://www.homedepot.com/p/204284538).
The retailer's [dimension sheet](https://images.thdstatic.com/catalog/pdfImages/13/1353fc43-4c14-45d4-ba92-5745b045eae3.pdf)
and listing filters give a 1/4-in pattern with approximately **0.312-in
ID, 0.734-in OD and 0.065-in thickness**. Use one beneath **each** bolt
head and nut in the trial stack. The 2024 NDS §12.1.3.3 requires a
standard cut washer or equal/larger metal plate or strap at both ends;
retail dimensions and the name “flat washer” alone do not prove that
classification or the required bearing/stiffness behavior. The earlier
5/8-in-OD Hillman cost illustration is a different, smaller pattern,
not a qualified substitute. The CAD's 1-in washer envelope was also only
a clearance proxy. Nut dimensions and actual projection still need a
complete stack check.

The [2024 NDS](https://awc.org/resources/2024-nds/) §12.3.6.2 requires a
valid bending-yield basis; §§12.3.7.1–.2 control when thread-root versus
full-body diameter may be used in bearing. Its Table 12.3.1B footnote 1
has a [published erratum](https://awc.org/wp-content/uploads/2026/03/2024-NDS-Errata-and-Addenda-03.23.26.pdf)
for nominal 1/4-in threaded fasteners whose effective root falls below
1/4 in. Its rendered Table 12.3.1B gives `K_D = 10D + 0.5` for
`0.17 in < D < 0.25 in`; `D` is the effective calculation diameter under
§12.3.7, not an assumed nominal shank. A PDF text extraction can misread
the plus sign, so use the rendered AWC table. The official [2024 NDS
Appendix I and L](https://web-media.awc.org/wp-content/uploads/2021/12/17210019/AWC_NDS2024_withCommentary_20240719_AWCWebsite_Appendix.pdf)
give a **45,000-psi Fyb reference for bolts as a class** in Table I1 and
a **typical 0.189-in root** for nominal 1/4-in standard hex bolts in
Table L1. The 3/8-in qualifier in I1 attaches to *lag screws*, not bolts.
These are now available **conditional inputs** for a quarter-inch bolt
calculation; L1 does not certify an exact minimum delivered root, and I1
does not identify this A307 lot. The generic
[ASTM A307 Grade A mechanical-property summary](https://www.portlandbolt.com/technical/specifications/astm-a307/)
gives a 60-ksi minimum tensile strength but no minimum yield strength.
Neither that tensile minimum nor a generic UNC-2A thread class is a measured
product-specific root or a complete NDS lateral-joint resistance.

The short Grade 8 listing illustrates why a material standard can help
without qualifying a joint. A [manufacturer's SAE J429 table](https://www.portlandbolt.com/technical/faqs/j429-strength-requirements/)
lists 130-ksi minimum tensile yield and 150-ksi minimum ultimate for
1/4-in Grade 8. An [AWC bolt commentary approximation](https://awc.org/wp-content/uploads/2021/10/AWC_NDS2018-withCommentary_20210113_AWCWebsite_Appendix.pdf)
uses their mean, 140 ksi, as a candidate dowel bending-yield input for
conforming material. This is not a lot-specific bending test or permission
to apply those properties to the longer A307 retail leads. A generic
UNC-2A thread chart likewise cannot prove the delivered root diameter or
where its threads land within each timber member. No located 5-in/8-in
ordinary-store SKU presently combines adequate length, supported
bending-yield input, and controlled thread/root data.

For a conditional numerical component comparison, carry the NDS class
reference Fyb and typical root transparently, with root sensitivity and
no selected-product verdict. Before releasing actual sizing, obtain a
controlled root or minor-diameter range for the exact model and confirm
the NDS bending-yield basis applies to the delivered product,
actual shank/thread occupancy in each member, sufficient nut engagement,
washer bearing inputs, and same-case combined actions. No manufacturer
contact or purchase is authorized by this screen.
