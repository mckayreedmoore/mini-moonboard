# PB04 retail hardware tolerance basis: 8-inch outer upright stacks

Status: **no verified worst-case pocket depth or hardware release**. Checked
2026-09-21 from standards publishers, fastener manufacturers, and retailer pages.
No supplier contact, purchase, or physical measurement. This applies only to
PB04's twelve pocketed outer upright stacks, not every PB04 bolt.

## Named stack and scope of each claim

The PB04 trial uses an [Everbilt 800696 1/4-20 × 8-in zinc hex bolt][bolt],
one washer at each end, and a hex nut. The PB04 cost lead names
[Hillman 490622 1/4-20 zinc hex nut][nut]. For the modeled **0.734-in OD**
washer family, [Everbilt 807210 1/4-in zinc flat washer][washer] is a
retail lead: Home Depot filters place it at **0.734-in OD and 0.065-in
thickness**. Its [generic USS/SAE chart][hd-chart] gives the 1/4-in USS
pattern as 5/16-in ID, 0.734-in OD, 0.065-in thickness. The separate
Hillman 490687 washer in the PB04 cost illustration is listed at **5/8-in
OD**; it is not the modeled 0.734-in washer.

These are designations or nominal listing dimensions, not acceptance limits.
The bolt page lists **A307** and **6-in thread length**; neither field says
that model 800696 conforms dimensionally to a particular edition of ASME
B18.2.1, nor defines where complete usable threads begin and end. ASTM's
[A307 catalog][astm] describes chemical and mechanical requirements for
carbon-steel bolts; an A307 label alone is not a product-specific dimensional
certificate. Lowe's lists Hillman 490622 as 1/4-20 hex, while its **Grade**
field says “All-Purpose”; its general Grade 2 prose does not establish that
part's actual grade, ASME nut style, or height limits.

## Published dimensional routes versus this retail assembly

**Bolt length.** [ASME B18.2.1-2012 (R2021)][b18-bolt] covers inch hex
bolts. [Portland Bolt's rendition of its table][length] gives
**+0.10/−0.18 in** for a non-pointed 1/4–3/8-in hex bolt longer than 6 in.
Length is measured from [under the head to the end][measure]. This row
applies to 800696 *if* it is that product type and its supplier guarantees
that standard/edition. The listing does not. The pointed cap-screw row is
a different product type.

**Washer thickness.** [ASME B18.21.1][b18-washer] covers plain-washer
dimensions. A [Fastenal purchase specification][fast-washer] for its own
zinc, low-carbon, Type A wide/USS washer gives **0.051–0.080 in** at 1/4 in,
with 0.734-in basic OD. This is a toleranced family example, **not**
certification of Everbilt 807210. Home Depot's 0.065-in listing supplies no
807210 minimum or maximum.

**Nut height.** [ASME B18.2.2-2022][b18-nut] covers inch hex-nut dimensions.
A [Fastenal purchase specification][fast-nut] for a *different*,
hot-dip-galvanized 1/4-in hex nut gives **0.212–0.226 in**. It does not
identify Hillman 490622; Lowe's supplies neither 490622 height bounds nor
B18.2.2 conformance.

**Thread length and runout.** Home Depot lists **6 in** of thread for 800696.
[Portland Bolt][thread] distinguishes usable thread from runout and reports
no specified maximum runout for a standard hex bolt; its 1/4-in cap-screw
transition value belongs to a different product type. The retail thread
length does not locate the first complete usable thread. A generic B18.2.1
thread-length formula cannot certify this SKU's thread geometry.

**Tip protrusion.** The PB04 model reserves **two 1/4-20 pitches = 0.100 in
= 2.54 mm** beyond the nut's outer face. [AISC's RCSC FAQ][aisc] addresses
high-strength structural-steel joints and says contract documents can add
stick-through. Two pitches are a **PB04 design choice**, not an A307/Everbilt
property or verified wood-joint requirement. Incomplete/chamfered tip
threads cannot automatically count as two *full* projecting threads.

Home Depot's washer Q&A mixes product variants: an answer on the 807210
family page gives **0.086–0.132 in** for a question about a **0.049-in**
listing, which conflicts with the 0.065-in 807210 pattern. It does not
identify a 807210 lot or justify transferring those bounds to this stack.
The retailer's category “A307” filter on a washer is likewise not a
washer dimensional or material conformance statement.

## Pocket arithmetic and unresolved reserve

The PB04 model's source values are a **228.6-mm (9-in) wood grip**, two
**0.065-in** washers, a **0.226-in** nut envelope, an **8-in** bolt, and a
**two-pitch** tip projection. Its nominal equation is

`D₀ = G₀ + 2W₀ + H₀ + P₀ − L₀`

`= 228.6 + 2(1.651) + 5.7404 + 2.54 − 203.2 = 36.9824 mm`.

The detached **37.9824-mm** trial adds exactly **1.0000 mm nominal** depth.
That difference is geometric sensitivity, not a measured or specified
tolerance. For a worst-case minimum *as-cut* depth, the additive requirement
would be

`D_required = G_max + W_near,max + W_far,max + H_max + P_required − L_min`.

Relative to the 36.9824-mm model, add the grip increase, both washer
increases, nut-height increase, any higher required protrusion, and bolt
shortfall. A specified nominal cut depth must also add the maximum pocket
**undersize** error; alternatively check the measured minimum as-cut depth
directly. This equation addresses tip reach; a separate
thread-engagement check must show the nut's entire required bearing/thread
height lies on complete usable bolt threads, including the tip chamfer and
shank-side runout.

**Conditional check, not an Everbilt allowance:** if 800696 actually met the
ordinary non-pointed B18.2.1 length row above, its shortest length would be
**7.82 in = 198.628 mm**, a **4.572-mm** shortfall from nominal. Keeping
every other PB04 nominal input fixed would call for **41.5544 mm** depth;
the 37.9824-mm trial would then be **3.572 mm short**. This is only one
conditional term, not a full worst-case stack or a claim that a delivered
800696 bolt can or will have that length. The Fastenal washer/nut intervals
must not be silently added as Everbilt/Hillman bounds.

No finite, product-backed additive reserve can be calculated for **either**
36.9824 or 37.9824 mm from the reviewed sources. The exact missing inputs
are: an 800696 factory drawing or supplier commitment to its **under-head
length min/max**, product type/ASME edition, **first and last complete usable
thread positions** (including runout and tip chamfer); 807210 **thickness
min/max** for each washer; 490622 **height min/max** and effective threaded
height; the maximum installed wood grip; minimum achieved pocket depth
after machining; and the project's required definition of thread protrusion
and engagement. Until those are bounded for the actual parts and cut, neither
pocket depth is a verified fit.

[bolt]: https://www.homedepot.com/p/204281626
[nut]: https://www.lowes.com/pd/Hillman-1-4-in-x-20-Zinc-Plated-Steel-Hex-Nut/1001265718
[washer]: https://www.homedepot.com/p/204284538
[hd-chart]: https://www.homedepot.com/catalog/pdfImages/4a/4a362438-0e50-481c-af25-7f98aa28c057.pdf
[astm]: https://store.astm.org/a0307-21.html
[b18-bolt]: https://www.asme.org/codes-standards/find-codes-standards/b18-2-1-square-hex-heavy-hex-askew-head-bolts-hex-heavy-hex-hex-flange-lobed-head-lag-screws
[length]: https://www.portlandbolt.com/technical/faqs/bolt-length-tolerance/
[measure]: https://www.portlandbolt.com/technical/faqs/turn-nut-method/
[b18-washer]: https://www.asme.org/codes-standards/find-codes-standards/b18-21-1-washers-helical-spring-lock-tooth-lock-plain-washers
[fast-washer]: https://www.fastenal.com/content/product_specifications/FW.LC.USS.A.Z.00.pdf
[b18-nut]: https://www.asme.org/codes-standards/find-codes-standards/b18-2-2-nuts-general-applications-machine-screw-nuts-hex-square-hex-flange-coupling-nuts
[fast-nut]: https://www.fastenal.com/content/product_specifications/UBOLT.LT.4FHN.HDG.08.pdf
[thread]: https://www.portlandbolt.com/technical/faqs/thread-runout/
[aisc]: https://www.aisc.org/aisc/solutions-center/engineering-faqs/6-bolting/
