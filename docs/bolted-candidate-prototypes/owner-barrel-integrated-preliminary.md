# Integrated barrel frame: first current-joint numerical screen

The [live calculation](../../scripts/owner_barrel_integrated_preliminary.py)
reads the maintained **integrated** barrel assembly, not the earlier
outward-post/backer layout. It checks one lower outer rail duty and the
single-bolt right center principal/header duty. The left center is mirrored;
the other 22 duties are **not** assessed here. Both use conditional dry,
unincised DF-L No. 2 inputs from the [2024 NDS material record](../bolted-candidate-material-basis.json).
The [American Wood Council](https://awc.org/resources/2024-nds-supplement/)
warns not to mix provisions and values from different NDS editions. Delivered
lumber and hardware are not verified. These are component sensitivities,
**not complete-joint design values, a frame rating, or a fabrication release**.

| Current modeled joint | Geometry and conditional component scale | Critical missing path |
| --- | --- | --- |
| Lower right outer rail to right side, `clip_horizontal_lower_right_2` | Two 6-in bolts, 32.25 mm pitch, barrels 60 mm from the rail end; each nominal tip is only 1.849 mm past the assumed thread axis and 3.155 mm **short of the far barrel wall**. Ideal full-contact washer/wood `Fc⊥` reference is 1.993 kN **per bolt**. A deliberately isolated two-full-slot parallel-tension sensitivity is 18.078 kN for the rail section. Typical-root, steel-only axial `EA/L` is 24.65 kN/mm per bolt. | Real thread start/span and barrel strength; two-row action sharing, rail cut section and breakout; signed case forces and moment. Neither two washer references nor the slot scale may be summed into a joint resistance. |
| Center right principal to base header, `clip_split_base_center_right` | One angled 5-in bolt and barrel, 19.05 mm trial washer, 14.046 mm nominal principal X-edge ligament, 41.300 mm barrel recess. The tip extends 20.345 mm **past** the barrel far wall inside the modeled bore. The header head pocket leaves only 2.092 mm nominal edge stock. Ideal full-contact washer/wood `Fc⊥` reference is 1.038 kN. A one-full-slot section sensitivity is 19.590 kN, and typical-root steel-only `EA/L` is 36.50 kN/mm. | The actual blind-cut section, pocket splitting, barrel breakout, open far-side thread path, and the compression/contact path needed for moment or twist. One point fastener alone supplies no free resisting couple. |

The NDS [connection calculator](https://awc.org/resources/connection-calculator/)
addresses ordinary single-bolt and other listed fasteners; its lateral-bolt
result does not qualify a buried cross-dowel, axial thread path, pocket,
or complete demountable joint. The rail's 18.078 kN calculation treats two
full through-width slots in a 38.1 × 139.7 mm section; the actual rail has
blind cuts and other openings. The center's 19.590 kN scale treats one full
slot, not the actual service-bored, blind-cut principal. Both are *sizing*
numbers only. The washer numbers assume a stiff, fully seated, correctly
sized washer on sound wood; no such purchased washer is selected. Steel-only
`EA/L` uses hypothetical 205 GPa modulus and a typical 0.189-in thread root;
it omits thread, barrel, wood, seating, hole play and slip. The 2024 DF-L
dowel-bearing inputs (5,600 psi parallel; 4,450 psi perpendicular at 1/4 in)
are wood properties, not barrel-joint resistances.

For a two-point rail *sensitivity* under a signed in-plane force `F` and
moment `M`, an equal-stiffness idealization gives row actions
`F/2 ± M/32.25 mm`. No new-topology `F` or `M` is available yet, and contact,
slip or unequal stiffness could change that distribution. At the center,
a single bolt acting at one point cannot resolve an arbitrary free moment;
the actual butt-face compression and the connected frame would have to form
the couple. Opening or reversed twist can remove that compression, so a
clearance-free pose does not establish mechanical plausibility in all cases.

The [source-built gross-face input](../../scripts/owner_barrel_native_face_contacts.py)
adds the actual uncut contact geometry to those conditional components. The
representative rail face is **5,322.57 mm²**. The center principal/header
face is **5,113.122 mm²**, and its sole bolt crosses **50.907 mm rearward**
of the gross-face centroid. Only **16.195 mm** of that face lies behind the
bolt, versus **118.008 mm** ahead. The bolt's axial direction has an absolute
**0.766** projection onto the contact normal, so it also has a substantial
in-plane component. A 2×2 face grid would put every compression-cell center
ahead of this bolt and miss the narrow rear strip; the current geometry input
uses 2×8 cells at each single-bolt center duty. These are **geometric
lever-arm bounds**, not moment resistance or stiffness. Drilled section loss,
wood orientation, contact opening, barrel breakout, and signed demand must
still be calculated before a two-way resisting couple can be claimed.

The next numerical step is a **signed six-case integrated response** with
opening/contact and joint slip represented, followed by the actual cut-wood
and barrel/thread limit states for all 24 duties. The selected angle frame's
old forces are not demands for this topology. Before an exploratory physical
coupon, select one delivered bolt/barrel/washer/wood lot, measure usable
thread engagement and complete the center pocket/LED-feed and rail fit gates.
No load, drilling, fabrication or climbing acceptance is claimed.
