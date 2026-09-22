# Integrated center principal/header: preliminary components

**Conditional numerical screen only.** The
[calculation](../../scripts/owner_barrel_integrated_center_prelim.py)
reads the [revised CAD joint](../../scripts/owner_barrel_center_post_joint_replan.py),
not a native force solve. It uses the repository's dry DF-L No. 2 inputs from
the [2024 NDS](https://awc.org/resources/2024-nds/) and matching
[2024 Supplement](https://awc.org/resources/2024-nds-supplement/), with the
[2024 errata](https://awc.org/wp-content/uploads/2026/03/2024-NDS-Errata-and-Addenda-03.23.26.pdf).
Actual stock and purchased hardware are unverified. None of these values is a joint rating.

The right principal/header station represents the mirrored pair. Two bolts enter
recesses in the header's rear face and reach barrels in the 38.1 × 139.7 mm
principal. The 127.0 and 114.3 mm bolts have 23.893 and 13.003 mm of modeled
header path, then 76.107 and 86.997 mm of principal path to their assumed
thread axes. Each bore ends 4.0 mm beyond its nominal tip. The axes are
20.706 mm apart perpendicular to the bolts. The opposing 17.051 mm blind
barrel bores leave a nominal 3.998 mm X gap between their caps; each barrel
has just 1.049 mm of entry recess. Fit and tolerance remain open.
The nominal tips are 20.345 and 7.645 mm beyond the modeled barrel far wall.
The delivered barrel's through-thread/open far exit and usable bolt passage
are unknown; the 4 mm wood-bore clearance does not prove this fit.

- **Bolt shaft:** 31.669 mm² nominal 6.35 mm shank area; 18.100 mm² at the
  *typical* 0.189 in root. Axial force sensitivity is `A_t × verified stress`.
  Delivered root, tensile/shear strength, thread exposure and combined stress
  remain unknown.
- **Header washer/wood:** 1.038 kN per bolt at ideal full contact and 625 psi
  `Fc⊥`. Washer rigidity, seat contact, prying and adjustments are unknown.
- **Dowel bearing inputs:** 5,600 psi parallel and 4,450 psi perpendicular at
  6.35 mm; 4,650 psi at the typical root. These are wood inputs, not a joint
  value; actual grain/load direction and shaft/root bearing need proof.
- **Ordinary wood/wood yield surrogate:** 444.196 N for row 1 (Mode IV),
  352.017 N for row 2 (Mode IIIm). Both checked normal-to-axis lateral
  directions give the same numbers. Inputs are 2024 NDS Appendix I's
  conditional 45,000 psi bolt-class `F_yb`, Appendix L's typical root and
  zero gap. Bearing lengths are centerline lengths: the angled butt clips
  the per-member bore cylinders. The buried barrel joint is outside this
  complete-joint model.
- **Barrel body/thread:** the 3.998 mm bore-cap gap is geometry only. Barrel
  bending, thread strip, wall bearing, principal breakout and metal rating
  remain unknown.
- **Principal net section:** 5,034.615 mm² smallest sampled cut area versus
  5,322.570 mm² gross. The 19.960 kN `Ft × sampled area` scale is unadjusted
  parallel tension, not local breakout or joint resistance. A hypothetical
  two-full-slot Appendix E helper gives 18.078 kN; it is not the blind-cut
  section.
- **Axial withdrawal:** no value. Wood-screw withdrawal equations do not rate
  a machine bolt threaded into a steel barrel. The full path includes shaft,
  threads, barrel, barrel-to-wood and washer/wood modes.
- **Stiffness:** steel-only `EA/L` is 63.867 kN/mm at nominal shank and
  36.503 kN/mm at typical root, assuming `E=205,000 MPa` and `L=101.651 mm`.
  Wood seating, thread play, barrel compliance, contact and cyclic slip are
  unknown. The 2024 NDS group-modulus comparison is 3.940 kN/mm per bolt,
  not this joint's spring.
- **Group action:** 20.706 mm perpendicular-axis pitch. No two-bolt sum,
  load-share factor, moment distribution or classified placement verdict.

The net-area sample cuts both principal machine bores and both blind barrel
bores, then samples X–N sections every 0.5 mm near the barrels. It is not a
global section search or a splitting/tear-out model. The apparent 19.960 kN
scale cannot be compared with the surrogate yield numbers as a controlling
joint capacity. The NDS ordinary wood/wood yield modes require their own
applicability conditions; see the [barrel applicability note](owner-barrel-nds-applicability.md).

Still needed: signed new-topology forces and moments with contact and unequal
bolt sharing; controlled bolt root, thread length and steel properties;
identified barrel material, thread engagement and resistance; inspected wood
and actual cuts; washer product and seating; local splitting, breakout,
net-section and group checks; and measured slip/tolerance/reassembly behavior.
No actual demand, utilization, complete stiffness or resistance is available.
No native solve, drilling, fabrication or structural release.
