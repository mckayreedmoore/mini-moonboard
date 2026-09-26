# Orderable ordinary-washer candidates and yield-property gap

**Checked:** 2026-09-25. **Scope:** 1/4-in flat washers for the current
ordinary WJ24 stacks. **Status:** no single public offer found that both
guarantees the pinned Type A Wide dimensional envelope and directly binds an
orderable product to a numeric minimum yield property. The options below are
bounded conditional candidates, not selected or received parts.

## Controlling washer envelope

The ordinary stack uses two 1/4-in Type A Wide washers per bolt. Its pinned
dimensions are ID 0.307–0.327 in, OD 0.727–0.749 in, and thickness
0.051–0.080 in, as recorded in the
[ordinary nut/washer property basis](../current-ordinary-nut-washer-property-basis.md).
The ranges come from the published Type A Wide size table and are the
comparison envelope here; nominal size labels alone are insufficient.

## Best orderable dimensional lead: 316 Type A Wide, yield not published

MF Supply lists [WF14S3, 1/4 USS flat washer, 316 stainless steel](https://www.mfsupply.com/1-4-USS-Flat-Washer-316-Stainless-Steel-p/wf14s3.htm),
cross-reference `14WUSS316`, to ASME B18.21.1. The page displayed $140.40 per
box ($0.1404 each), stock-item status, and 14 boxes available. The ratio of
the displayed box and piece prices, and the stated 6.7-lb box / 0.0067-lb
piece weights, imply 1,000 pieces per box; the page does not explicitly label
the pack count. No vendor contact or order was made.

For 48 ordinary axes at two washers each, the scenario quantity is 96. One
box would cover that quantity if the implied 1,000-piece pack is correct; its
displayed purchase price is $140.40. This page identifies 316 material and
ASME B18.21.1, but does not publish a numeric yield value, identify ASTM
A240/A276 or a condition, or give lot-level property certification. The
[Fastenal 316 USS product standard](https://www.fastenal.com/content/product_specifications/FW.USS.316.03.pdf)
confirms that a 1/4-in Type A Wide 316 product standard uses the pinned
dimensions, but it is not the MF Supply SKU's material certificate or a
yield specification. Therefore `WF14S3` is a dimensionally promising
orderable source, not a yield-qualified washer for the conditional bending
scenario.

## Near-match with an explicit material-quality reference

Grainger lists [2DPA8 / WAS50514, USS 316 stainless flat washer](https://www.grainger.com/product/USS-Washer-316-2DPA8)
in 25-packs at $15.75 per pack. Its product page identifies ASTM A276 as the
material quality standard, lists 75,000 psi tensile strength and 83 HRB, and
states an ANSI B18.21.1 dimensional standard. Its dimensional listing,
however, gives ID 0.312 ±0.010 in and OD 0.750 ±0.010 in. Compared with the
pinned envelope, the permitted ID intersection is only 0.307–0.322 in, the
OD intersection is only 0.740–0.749 in, and the full listed thickness range
0.051–0.080 in matches. The linked [Grainger drawing](https://www.grainger.com/ec/pdf/grainger-2DPA8_v1.pdf)
shows nominal ID 0.312 in, OD 0.750 in, and thickness 0.080 in without
tolerances. The product's stated tolerances do not guarantee all actual
units fall inside the WJ24 dimensional envelope; per-part dimensional
measurement would be needed to identify conforming pieces.

As a conditional material reference, Rolled Alloys' [316/316L data sheet](https://www.rolledalloys.com/wp-content/uploads/316-316L_Stainless_DataSheet_RolledAlloys.pdf)
reports a 30 ksi minimum 0.2% yield strength for Type 316 under ASTM A240,
Condition A; its other data sheet also lists 30 ksi minimum under ASTM A276.
ASTM's [A276/A276M-24 scope](https://store.astm.org/a0276_a0276m-24.html)
covers stainless bars and shapes and requires tensile/yield mechanical
testing. Grainger's A276 product-quality field creates a possible conditional
property chain, but the individual washer page omits material condition and
stock form, and does not publish yield itself. Do not treat the 30 ksi table
value as an established 2DPA8 lot minimum. For 96 washers, four 25-packs
would cost $63.00 and leave four surplus, assuming availability at the
displayed price; dimensional fit and the material-property chain remain
unresolved.

## Other bounded leads

| Lead | Published offer | Boundary |
| --- | --- | --- |
| RAYCHIN 254 SMO USS flat-washer family | Manufacturer states Type 254 SMO / UNS S31254, solution-annealed and water-quenched washers, minimum `Rp0.2 = 310 MPa (45 ksi)`, and USS sizes starting at 1/4 in. | This is a usable **family-level conditional yield input** only if a specifically offered 1/4-in Type A Wide part carries that material/condition and meets the pinned dimensions. It is quote-only with no public SKU, pack quantity, or price. See [prior yield-property option note](ordinary-washer-yield-options.md). |
| K.L. Jack `25NWUS` | Plain low-carbon 1/4-in Type A Wide listing; existing ordinary hardware note records $3.47 per 100-piece box. | No numeric material grade, condition, tensile strength, or yield minimum. |
| K.L. Jack `25NWUS8Z` | 1/4-in Type A Wide, ASTM F436, quenched-and-tempered, 38–45 HRC. | Hardness alone does not give the yield minimum used here; no hardness-to-yield conversion is made. |
| McMaster-Carr `98026A029` | Orderable USS zinc-yellow-chromate steel washer for 1/4-in screw, nominal ID .312, OD .734, thickness .051–.080; pack 100; page identifies fastener Grade 8. | Dimensions are promising, but the offer provides no numeric yield minimum. A washer's Grade 8 compatibility label is not a numeric washer yield value. |
| Louisiana DOTD 2016 construction specification | Its section 821.07.8 calls for Type 304/316 flat washers with minimum 80 ksi tensile and 40 ksi yield, using Type A Wide for oversized holes. | This is a published material-performance specification, not a product offer or SKU. It does not establish that any listed candidate conforms. |

## Conditional-use decision

The existing 254 SMO family source is sufficient to define a *conditional
material-yield scenario* at 310 MPa, provided the modeled candidate is
explicitly a solution-annealed 254 SMO washer and its standard dimensions are
assumed to meet the pinned envelope. It is not enough to assign that value to
an orderable product today: the manufacturer publishes no SKU, package
quantity, or price. The orderable MF Supply 316 item is the strongest exact
standard/dimensional lead found, but lacks its own yield/material-condition
statement. The Grainger listing has a possible A276 property chain but
neither guaranteed dimensions nor a product-condition bound. None supports
a selected all-stack product or a washer-bending resistance; yield is only a
material input, and a separate supported plate/contact method is still
required.

Stripe Directory was attempted before the supplier-page lookup. The
installed CLI is 1.33.0 and `stripe directory --help` returns “Unknown
command”; the official [Directory setup page](https://stripe.directory)
instructs users to install or upgrade the CLI and install its Directory
plugin. The current environment did not expose a working Directory command,
so the documented public-source fallback was used. No external party was
contacted, credentials were not changed, and no purchase was made.
