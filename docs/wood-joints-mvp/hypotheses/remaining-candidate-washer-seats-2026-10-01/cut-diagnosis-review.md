# Independent review: remaining washer-seat cut diagnosis

Review scope: the single `center_principal_right_2` nut-seat exception in the
remaining-seat packet. This review independently traces the neighboring cut,
computes the washer-annulus overlap, and compares that area with a direct
Boolean against the hash-bound finished STEP. It does not recreate the other
107 seat results, assess bearing resistance, or change any geometry.

The source inventory identifies the wood-joints candidate as
`compact-floor-flush-wood-joints-development`, based on
`compact-floor-flush-development` with the `kerf-right` width variant. Its
hash is
`07af4c3eb642cf3887595fe4415eb65404cdcf74d66c5c7bb182847ef21c2d78`. In the
hash-bound
[`timber-passages.json`](../../../floor-flush-construction-kerf-right/timber-passages.json)
(`5c86941458a6a92432941fdf7e13b2b21ef2f933332e0e1ec602d4d57796f15f`),
`bore_base_principal_center_right_072` is on
`base_principal_center_right`, with datums F1/G1. The record specifies an
X-directed, 38.1 mm diameter passage starting at
`(49.94999999999991, -72.95548222202063, 348.1769448188469)` mm and running
40.100000000000186 mm. It enters at x=`50.94999999999982` mm and exits at
x=`89.0500000000001` mm. The source describes this passage as not qualified
for machining.

The kerf-right adapter ([`floor_flush_width.py`](../../../../mini_moonboard/floor_flush_width.py),
SHA-256 `1dc0b6cc6d1bd10ae8cffaaa707fa25bdcd264783dcb9ec59cf8b911a6512de5`)
translates a fixed list of outer-right parts; it does
not include `base_principal_center_right` in that list. The target member also
does not appear in the adapter's X-max trim list. Thus this F1/G1 cut receives
no kerf translation or trim. The source record's `start_mm` extends one
millimeter beyond the 38.1 mm member at both ends; it is a through-cut
construction envelope, not an added one-millimeter coordinate shift of the
seat or bore axis.

For axis `center_principal_right_2`, the nut seat lies at
`(50.95, -90.30983137880766, 367.0102220661388)` mm, with inward direction
`+X`. The finished-solid binding and file both hash to
`9053a7210a781e919038a4a823f867325dd5c78907bd028d8b9e76dc0b46df58`. Direct
STEP inspection found a radius-19.05 mm cylindrical face, directed along
`+X`, with axis location `(49.95, -72.95548222202, 348.17694481884)` mm. Its
axis is within `6.91e-12` mm of the service-cut record and its axial bounds
are x=`50.95..89.05` mm. This independently ties the BREP opening to the
F1/G1 service passage at the washer plane.

For the CAD annulus, `R_o=9.3218` mm and `R_i=4` mm. The passage radius is
`R_b=19.05` mm and its in-plane center distance from the washer is
`d=25.609876347398426` mm. The two disk intersections give:

| Quantity | Area |
| --- | ---: |
| Passage disk ∩ washer outer disk, `I(R_b,R_o,d)` | 21.148666401715 mm² |
| Passage disk ∩ washer inner disk, `I(R_b,R_i,d)` | 0 mm² |
| Lost annulus support | 21.148666401715 mm² |
| Total CAD annulus, `π(R_o²−R_i²)` | 222.7262121512 mm² |
| Supported fraction | 90.5046351763% |

The zero inner-disk overlap follows from `d > R_b + R_i` (`25.6099 > 23.05`),
while the outer disks overlap because `d < R_b + R_o` (`25.6099 < 28.3718`).
I evaluated the standard two-circle lens formula directly, independently of
the packet's circle-area helper.

I also imported the exact STEP and intersected the CAD annulus extruded inward
along `+X` with the solid. Dividing the missing Boolean volume by probe depth
gave lost areas of `21.148666401691`, `21.148666401664`, and
`21.148666401650` mm² at depths 0.01, 0.05, and 0.1 mm, respectively. These
agree with the analytic result to better than `7e-11 mm²`; the small drift is
Boolean floating-point noise. The corresponding support fraction is
`0.90504635176` at all three depths.

The geometric exception is confirmed for this centered CAD annulus and this
finished STEP. The review does not establish a pressure distribution,
washer-metal bending, wood bearing resistance, or contact behavior for a
partially supported washer. The pinned checker SHA-256 during this review was
`a3cedb8e6fddf9d4080afd82cf12cf3e5a39658868baa478ad1f14eee7d07967`.
