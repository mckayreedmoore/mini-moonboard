# Ordinary-size washer yield-property options

**Checked:** 2026-09-25. **Status:** conditional material-property option for
the current 1/4-20 washer role. This note does not select a replacement,
change geometry, establish a washer resistance, or qualify delivered parts.

## Result

The current plain low-carbon Type A Wide washer basis still has no published
numeric yield minimum. A same-size material-class alternative with a direct
published yield value is available as a supplier lead: RAYCHIN's 254 SMO
(UNS S31254) USS flat-washer family. The supplier lists 1/4-in USS washers,
all standard thickness series, and a minimum 0.2%-offset yield strength of
310 MPa (45 ksi) for its solution-annealed washer material. This is enough to
define a **conditional 254 SMO washer material input** for an MVP-E sensitivity
or direct-material-yield scenario, if the item is explicitly dimensioned and
specified to match the current Type A Wide stack. It does not supply a
washer-bending model, capacity, product SKU, delivered-part identity, or
price. The baseline 25NWUS / low-carbon washer case remains unresolved.

## Conditional option and limits

RAYCHIN's [254 SMO flat-washer page](https://www.ray-chin.com/Special-Fasteners/254-SMO-Fasteners/254-SMO-Flat-Washers.html)
describes 254 SMO USS washers as available from 1/4 in upward in standard
thickness series, made to its cited inch-series washer standard, and available
with traceability. It identifies UNS S31254 and states that its washers are
supplied solution annealed and water quenched. Its property table gives
minimum room-temperature `Rp0.2` of 310 MPa (45 ksi) and says the minima are
per ASTM A479 / EN 10088-3. The exact ASTM edition, item number, purchase
quantity, finish, and price are not published on that page; it directs buyers
to request a quote. No quote or contact was made.

The manufacturer names ASME B18.22.1 for its inch-series USS washers. ASME's
[current B18.21.1 record](https://www.asme.org/codes-standards/find-codes-standards/b18-21-1-washers-helical-spring-lock-tooth-lock-plain-washers)
says the 2009 B18.21.1 edition consolidated B18.22.1-1965 and remains in
effect. The ordinary stack's Type A Wide dimensional envelope remains the
controlling check: ID 0.307–0.327 in, OD 0.727–0.749 in, and thickness
0.051–0.080 in (nominal 0.312 × 0.734 × 0.065 in), as recorded in the
[ordinary nut/washer property basis](../current-ordinary-nut-washer-property-basis.md)
and [ordinary hardware basis](../ordinary-hardware-basis.md). The RAYCHIN
page gives the 1/4-in USS class but not a part-specific dimensional table;
therefore compatibility is conditional on a specific offered part meeting
that envelope. Its “full traceability” statement is not a lot certificate
for a part not yet ordered or received.

Alleima's [254 SMO billet datasheet](https://integration.alleima.com/en/technical-center/material-datasheets/billets/alleima-254-smo-esr/)
independently lists `Rp0.2 ≥ 310 MPa` (`≥45 ksi`) in solution-annealed
condition, on separately solution-annealed and quenched test pieces. This
corroborates the material value, but it is not a certificate for a RAYCHIN
washer or for any delivered WJ24 part. Use 310 MPa only as the conditional
minimum material-yield input tied to this explicit candidate scenario; do not
assign it to 25NWUS, Würth 408.14, 25NWUS8Z, or unidentified washers.

No washer steel bending, spreading, dish, local-yield, or through-hole
resistance method is established in the [bolt resistance basis](../bolt-resistance-basis.md).
The direct yield value closes only the material-property input gap for this
alternate scenario. It does not create a resistance calculation or complete
joint result. The wood bearing check below a washer remains a separate
component. The exact material/temper of a made washer, actual geometry,
surface/contact behavior, and lot conformance remain unverified.

For the 48-axis 1/4-20 ordinary group, the current two-washer arrangement
would require 96 washers if this scenario were evaluated across that group.
RAYCHIN publishes neither a pack size nor price, so no package count or cost
delta can be calculated. This is not an order quantity or procurement plan.

## Screened non-solutions

| Lead | What is published | Why it does not resolve the current gap |
| --- | --- | --- |
| K.L. Jack `25NWUS` plain low-carbon Type A Wide | Matching dimensional range and “low carbon steel” | No grade, condition, hardness, tensile value, or yield minimum. |
| K.L. Jack `25NWUS8Z`, ASTM F436 | Same-size Type A Wide; quenched/tempered and 38–45 HRC | Hardness does not state yield; no hardness-to-yield conversion is used. |
| Würth `408.14` USS Grade 5 zinc washer | 1/4-in USS dimensions and product-page “Grade 5” description, as recorded in the [48-axis hardware basis](../current-ordinary-hardware-basis.md) | The page does not define a washer steel grade or publish yield. Bolt/nut Grade 5 terminology is not a washer yield property. |
| HexForge 310S washer page | Lists 1/4-in USS nominal geometry and yield values | The same page states a 292 MPa minimum yield in its introductory text and 205 MPa / 30 ksi in its mechanical table. It does not establish which value applies to the offered washer, so neither is adopted. |

## Search route and evidence boundary

The installed Stripe CLI is 1.33.0 and does not expose `stripe directory`
(`stripe directory --help` returns “Unknown command”). The current task's
supplier-property lookup therefore used the documented public-source fallback
after the Directory route was unavailable. The material search was limited to
direct manufacturer/supplier pages and the material-producer datasheet linked
above. No external party was contacted; no account credentials were changed;
no purchase was made.
