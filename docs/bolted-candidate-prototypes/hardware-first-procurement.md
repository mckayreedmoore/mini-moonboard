# HL35 hardware-first procurement evidence

Status: public-source screen, checked 2026-09-20. This is **not** a purchase list,
installed-joint qualification, bolt-length schedule, or fabrication/drilling release.
No sample, delivered hardware, local inventory, or actual stack has been inspected.

## Factory connector identity and conditions

- **Verified retail identity:** [Lowe's item 1944359](https://www.lowes.com/pd/Simpson-Strong-Tie-HL-3-1-4-in-x-5-in-Galvanized-Heavy-Angle-10-Qty/1002693778)
  and [Home Depot item 100374913](https://www.homedepot.com/p/100374913)
  both identify a Simpson **HL35-R**, 3-1/4 × 3-1/4 × 5 in, galvanized
  heavy angle. Lowe's states 7-gauge G90, one angle per package, and 1/2-in
  bolts; nuts and bolts are not listed as included. The old
  [Lowe's HL35 page](https://www.lowes.com/pd/Simpson-Strong-Tie-Wood-to-Wood-Heavy-Angle/3037134)
  identifies model HL35 but says it is no longer sold there.
- **Supported, not proven exact equivalence:** Simpson's response on the
  [HL35-R hole-spacing question](https://www.lowes.com/questions/simpson-strong-tie-hl35-r-angles-brackets-and-braces/1002693778/8250e297-9f65-5443-8b75-322144244762)
  directs the buyer to its HL catalog drawing. This is direct manufacturer
  support for using the catalog's nominal HL35 pattern to screen HL35-R;
  it does not provide factory tolerances, a delivered-part measurement, or
  an explicit HL35/HL35-R certification. Do not drill from a retailer photo.
- **Catalog conditions:** The [Simpson C-C-2026 HL page](https://dhcsupplies.s3.us-east-2.amazonaws.com/Documents/simpson-strong-tie/hl-angles.pdf)
  gives HL35 four specified 1/2-in through-bolts per angle, minimum
  3-1/2-in wood thickness for the 3/5 series, angle centered on a member
  face at least as wide as the angle, and bolts at least ASTM A307 Grade A.
  Its nominal drawing has D1 = 1-1/4 in, D2 = 2-1/2 in, and D3 = 2 in.
  One angle has DF/SP tabulated uplift 740 lb and F1 1,310 lb at the
  catalog's `(160)` basis. Two opposing angles are needed for F1 in both
  directions; the catalog permits doubling uplift for two, **not** lateral
  capacity. The [C-C-2026 general notes](https://www.rbscorp.com/wp-content/uploads/2026/03/C-C-2026.pdf)
  (pp. 21–23, 289) define `(160)` as wind/earthquake/uplift duration,
  require all specified fasteners, and provide an interaction equation for
  simultaneous *listed* force directions. HL35 has no published F2 or
  independent flange-couple rating; the roof-to-wall 75% shortcut is not
  an HL35 rule. These table values cannot be transferred to the board's
  sustained/combined wrench or divided by 1.6 to invent another rating.

## Retail through-bolt, nut, and washer leads

| Item | Publicly verified | Unresolved before selection |
| --- | --- | --- |
| [Prime-Line 9060913 at Home Depot](https://www.homedepot.com/p/310465135) | 1/2-13 × 6-in hex through-bolt, advertised ASTM A307 Grade A, ASME B18.2.1, hot-dip galvanized, 25-pack | Page also says `Fastener Plating: Uncoated`; finish must be checked on delivered item. A review reports a shorter measured length, which is a warning, not a verified dimension. Shank/thread distribution and installed grip remain unknown. |
| [Prime-Line 9060949 at Home Depot](https://www.homedepot.com/p/310465137) | 1/2-13 × 8-in hex through-bolt, advertised ASTM A307 Grade A and ASME B18.2.1, zinc plated, 10-pack | Page also says `Fastener Plating: Uncoated`; finish and delivered unthreaded grip unknown. |
| [Prime-Line 9061025 at Home Depot](https://www.homedepot.com/p/310465147) | 1/2-13 × 12-in hex through-bolt, advertised ASTM A307 Grade A, zinc plated, 5-pack | Length is only a retail lead; no 12-in stack or shank requirement established. |
| [Everbilt 804070 nut](https://www.homedepot.com/p/204274106) | 1/2-13 hot-dip galvanized hex nut, 50-pack, listed Grade 2 | Grade 2 is not a documented ASTM A563 grade. Verify actual nut grade, coating/thread fit, and joint specification; do not infer structural adequacy from matching nominal thread. |
| [Everbilt 807300 washer](https://www.homedepot.com/p/204284546) | 1/2-in galvanized flat washer, 50-pack | Retail page does not establish the outside diameter/thickness needed to compare with the NDS standard cut washer; measure or obtain a dimensional specification. |

Lowe's also offers a [Hillman 810512 1/2-13 galvanized nut](https://www.lowes.com/pd/1-2-in-x-13-Galvanized-Steel-Hex-Nut/3037536)
and [Hillman 492026 1/2-in galvanized washer](https://www.lowes.com/pd/Project-Pak-25-Count-1-2-in-x-Galvanized-Uncoated-Standard-SAE-Flat-Washer/3033314).
Those listings establish retail existence, not a fully specified structural
assembly or required washer dimensions. Online availability is not a claim
that a particular nearby store has stock. Common retail bolt grades or
catalog bolt-shaft strengths alone cannot qualify the wood/steel joint.

The [2024 NDS chapter 12, §12.1.3](https://awc.org/wp-content/uploads/2026/08/AWC_NDS2024_withCommentary_20250328_WebsiteChapter-12-%E2%80%93-Dowel-type-fasteners.pdf)
calls for standard ASME B18.2.1 bolts, aligned holes 1/32–1/16 in larger
than bolt diameter (nominal 17/32–9/16 in for 1/2-in bolts), and a standard
cut washer or equal/larger metal plate/strap between wood and the bolt head
and between wood and the nut. This is a *wood-hole* range, not a verified
HL35 factory-hole diameter or a drill instruction. Confirm actual steel
hole, washer bearing and clearance, bolt grip, full nut engagement, finish,
edge/end distances, and the installed load path before a specific length or
washer can be selected. Use one NDS edition consistently for the later
wood-connection checks.
