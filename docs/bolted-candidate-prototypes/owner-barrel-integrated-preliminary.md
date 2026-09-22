# Integrated barrel frame: first current-joint numerical screen

The [four-duty calculation](../../scripts/owner_barrel_integrated_preliminary.py)
and [center-post calculation](../../scripts/owner_barrel_post_header_preliminary.py)
read the maintained **integrated** barrel assembly, not the earlier
outward-post/backer layout. It checks one lower outer rail duty, the
single-bolt right center principal/header duty, **both center post/header
duties**, and both recessed outer header/post duties. The left principal is
mirrored; the other 18 duties are **not** assessed here. All six use
conditional dry, unincised DF-L No. 2 inputs from the
[2024 NDS material record](../bolted-candidate-material-basis.json).
The [American Wood Council](https://awc.org/resources/2024-nds-supplement/)
warns not to mix provisions and values from different NDS editions. Delivered
lumber and hardware are not verified. These are component sensitivities,
**not complete-joint design values, a frame rating, or a fabrication release**.

| Current modeled joint | Geometry and conditional component scale | Critical missing path |
| --- | --- | --- |
| Lower right outer rail to right side, `clip_horizontal_lower_right_2` | Two 6-in bolts, 32.25 mm pitch, barrels 60 mm from the rail end; each nominal tip is only 1.849 mm past the assumed thread axis and 3.155 mm **short of the far barrel wall**. Ideal full-contact washer/wood `Fc⊥` reference is 1.993 kN **per bolt**. A deliberately isolated two-full-slot parallel-tension sensitivity is 18.078 kN for the rail section. Typical-root, steel-only axial `EA/L` is 24.65 kN/mm per bolt. | Real thread start/span and barrel strength; two-row action sharing, rail cut section and breakout; signed case forces and moment. Neither two washer references nor the slot scale may be summed into a joint resistance. |
| Center right principal to base header, `clip_split_base_center_right` | One angled 4½-in trial bolt and barrel, 19.05 mm trial washer, 14.046 mm nominal principal X-edge ligament, 41.300 mm barrel recess. The tip extends 7.645 mm **past** the barrel far wall inside the modeled bore. The header head pocket leaves only 2.092 mm nominal edge stock. Ideal full-contact washer/wood `Fc⊥` reference is 1.038 kN. A one-full-slot section sensitivity is 19.590 kN, and typical-root steel-only `EA/L` is 36.50 kN/mm. | The actual blind-cut section, pocket splitting, barrel breakout, open far-side thread path, and the compression/contact path needed for moment or twist. One point fastener alone supplies no free resisting couple. |
| Center post to header, `clip_split_header_center_{left,right}` | Each seam-side post receives two fixed kicker screws with 45.2438 mm modeled embedment and joins the header by two 3½-in barrel bolts at 35 mm Y pitch. The post/header face is 12,419.33 mm² gross and 12,330.97 mm² after trial cuts. An ideal full-contact washer/wood `Fc⊥` reference is about 1.99 kN **per bolt**; typical-root steel-only `EA/L` is about 47.18 kN/mm. A two-full-slot post tension-section sensitivity is 42.18 kN, not the actual cut section. | Screw withdrawal/shear, post splitting, barrel/wood resistance, signed face contact, unequal row sharing and complete backing transfer. Neither embedment nor the isolated section scale rates the attachment. |
| Recessed outer header to left/right outer posts, `clip_timber_header_outer_{left,right}` | Each side has two 4½-in trial bolts at 50.0 mm Y pitch. Each modeled face has 5,322.57 mm² gross contact and 5,234.213 mm² after trial cuts; **6.35 mm** is the smallest modeled header-counterbore radial side stock. Conditional ideal full-contact header washer/wood `Fc⊥` is **1.993 kN per bolt**; an isolated two-full-slot post-section scale is **18.078 kN**, and typical-root steel-only `EA/L` is **35.99 kN/mm per bolt**. | The thin pocket side stock, post barrel bearing/breakout, real thread engagement, signed row sharing and the rim-first assembly/service sequence are unqualified. Neither washer reference nor full-slot scale is complete-joint resistance. |

The NDS [connection calculator](https://awc.org/resources/connection-calculator/)
addresses ordinary single-bolt and other listed fasteners; its lateral-bolt
result does not qualify a buried cross-dowel, axial thread path, pocket,
or complete demountable joint. The rail's 18.078 kN calculation treats two
full through-width slots in a 38.1 × 139.7 mm section; the actual rail has
blind cuts and other openings. The center's 19.590 kN scale treats one full
slot, not the actual service-bored, blind-cut principal. The outer-header
post's two-slot scale likewise omits the actual pocket and other cuts. All
are *sizing*
numbers only. The washer numbers assume a stiff, fully seated, correctly
sized washer on sound wood; no such purchased washer is selected. Steel-only
`EA/L` uses hypothetical 205 GPa modulus and a typical 0.189-in thread root;
it omits thread, barrel, wood, seating, hole play and slip. The 2024 DF-L
dowel-bearing inputs (5,600 psi parallel; 4,450 psi perpendicular at 1/4 in)
are wood properties, not barrel-joint resistances.

The [post/header backing screen](../../scripts/owner_barrel_post_header_preliminary.py)
also gives a unit-force load-path sensitivity. If a total 1 N global-Y force
were shared equally by a post's two fixed kicker screws, and the two barrel
bolts *alone* supplied a bilateral axial couple across their 35 mm pitch,
each row would need 3.2257 N of opposite axial action to balance the X
moment. Applied separately, the lower and upper screw axes imply 5.1114
and 1.3400 N per row per 1 N at that screw. Actual face contact, other
framing, bolt slip and force sharing are omitted. These coefficients are
**not** demands or joint capacities; the comparison with a washer reference
cannot establish an allowable kicker load.

At each outer header/post joint the two bolt axes are Z-directed and spaced
50 mm along Y. An equal-stiffness, contact-free pair would have axial row
actions `Fz/2 ± Mx/50 mm` for a moment about global X. This is only a
geometric sensitivity: actual contact opening, bearing, eccentricity, slip,
and unequal row stiffness can change it. The modeled **6.35 mm** pocket side
stock is especially sensitive to delivered washer/counterbore diameter and
drilling tolerance. It is not an edge-distance or splitting check.

For a two-point rail *sensitivity* under a signed in-plane force `F` and
moment `M`, an equal-stiffness idealization gives row actions
`F/2 ± M/32.25 mm`. No new-topology `F` or `M` is available yet, and contact,
slip or unequal stiffness could change that distribution. At the center,
a single bolt acting at one point cannot resolve an arbitrary free moment;
the actual butt-face compression and the connected frame would have to form
the couple. Opening or reversed twist can remove that compression, so a
clearance-free pose does not establish mechanical plausibility in all cases.

The [source-built face input](../../scripts/owner_barrel_native_face_contacts.py)
adds contact geometry to those conditional components. The representative
rail face is **5,322.57 mm² gross**, **5,234.213 mm²** after the viewer's
trial cuts. The center principal/header face is **5,113.122 mm² gross**,
**5,055.451 mm²** trial-cut, and its sole bolt crosses **50.907 mm rearward**
of the gross-face centroid. Only **16.195 mm** of that face lies behind the
bolt, versus **118.008 mm** ahead. The bolt's axial direction has an absolute
**0.766** projection onto the contact normal, so it also has a substantial
in-plane component. A 2×2 face grid would put every compression-cell center
ahead of this bolt and miss the narrow rear strip; the current geometry input
uses 2×8 cells at each single-bolt center duty. Exact cut-face clipping shows
**588.180 mm²** of face remaining behind each bolt line (11.63% of the cut
face), and the 16 center cell areas sum to that trial-cut face. The other 22
joints distribute measured cut-face area proportionally among four gross-grid
cells; this is **not exact local hole clipping**. These are **geometric
lever-arm and area bounds**, not moment resistance or stiffness. Cut-edge
pressure,
wood orientation, contact opening, barrel breakout, and signed demand must
still be calculated before a two-way resisting couple can be claimed.

The next numerical step is a **signed six-case integrated response** with
opening/contact and joint slip represented, followed by the actual cut-wood
and barrel/thread limit states for all 24 duties. The selected angle frame's
old forces are not demands for this topology. Before an exploratory physical
coupon, select one delivered bolt/barrel/washer/wood lot, measure usable
thread engagement and complete the center pocket/LED-feed and rail fit gates.
No load, drilling, fabrication or climbing acceptance is claimed.

All six required case identities (`a12-rear`, `a12-forward`, `a12-left`,
`k12-right`, `k12-rear`, `a1-rear`) now prepare from the same maintained
46-pair assembly using [conditional barrel/contact springs](../../scripts/owner_barrel_native_preparation.py).
Each preparation reports `native_solve: false` and `structural_released: false`.
This confirms input assembly, not a response, demand, stiffness, or pass.
