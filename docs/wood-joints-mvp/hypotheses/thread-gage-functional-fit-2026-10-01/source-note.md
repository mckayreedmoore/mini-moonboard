# What the bolt grip-gage limit says about nut engagement

**Status:** conditional dimensional derivation, 2026-10-01. It changes no
geometry, hardware selection, purchase, fit acceptance, capacity finding, or
modeled length. The standard arithmetic can narrow a coordinate comparison,
but does not establish functional nut engagement.

## Normative distinction

ASME B18.2.1-2012 §1.5 defines `LG` as the distance from the underhead
bearing surface to the face of the appropriate noncounterbored,
noncountersunk *special GO thread ring gage*, assembled by hand as far as the
thread permits. `LG,max` is an inspection criterion. This is a threaded gage,
not a plain length gauge, but §1.5 does not identify its working-thread length
or define `LG` as the coordinate of the first full-form thread. Section 2.5.2
separately gives the default external Class 2A limit before coating; where the
allowance is used for coating it caps coating thickness at one quarter of the
allowance and specifies basic-size Class 3A GO / Class 2A NOT GO gaging after
coating. Section 2.5.5 separately invokes B1.3 System 21 for thread
acceptability. Those thread-class and acceptance provisions do not make the
`LG` face coordinate a matched-nut travel or engagement limit.

The standard gives no basis here for treating the entire interval from
`LG,max` to minimum overall length as a GO-gage travel path. The special
gage's axial working-thread length is not stated in the `LG` definition; its
face at the far end of the screw is therefore not known to coincide with the
extreme tip. Accordingly, `LG,max ≤ a ≤ b ≤ L_min` below is only an
**endpoint coordinate enclosure**: when satisfied, the nut envelope `[a,b]`
lies between the tabulated maximum stopped-face coordinate and the minimum
tip coordinate. It does not show the gage traverses that envelope, that a nut can travel through
it, or that fully formed male thread covers it. B18.2.1 §1.5 calls the LG
device a threaded GO ring, so the text does not describe a plain length gauge;
however, §1.5 does not specify its working-thread profile/length or cite a
B1.2 gage designation. Section 1.6 lists B1.2 as a referenced standard, but
the explicit B1.2 Gage 3.1 cross-reference in §1.5 is for the separate point-
length measurement with a NOT GO major-diameter ring.

`LT` is expressly a reference dimension for calculation only. For a 1/4-in
cap screw longer than 6 in, Table 6 gives nominal `LT = 1.00 in`; it is not a
minimum one-inch full-form thread guarantee. `LB` measures to the last thread
scratch (or rolled-thread extrusion angle), not the first full thread or
usable threaded length. Section 1.5 defines point length from the extreme
point to the first fully formed thread at major diameter, measured by point
entry into a cylindrical NOT GO major-diameter ring gage (B1.2 Gage 3.1); that
definition supplies a measurement method, not a maximum point-length limit.
Section 2.4 requires screw products to have a chamfered point, says its angle
may vary, and leaves point features not defined by the product standard to
the manufacturer. I found no maximum axial point/chamfer length in §2.4 or
Table 6 examined. Table 13 limits total product length; §2.2 measures that
length from the bearing surface to the extreme end, including the point.
Neither provision bounds the first full-form thread from that point.

## Published primary-corner coordinate comparisons

The `[a,b]` values are the previously published full-outer-height envelope
for a **regular finished-hex nut scenario** with the packet's washer/nut
dimensional inputs, not measured hardware. They do not describe a washer-faced
nut or establish its contact face or usable internal-thread height. The local
candidate record calls K.L. Jack `25CNFH5Z` a finished hex nut; it is not
identified there as washer-faced. The B18.2.2 chamfer/contact limits are not
used in this derivation.

| Group and conditional length | Table 12 `LG,max / LB,min` | Published nut envelope `[a,b]` (mm) | Table 13 `L_min` | Endpoint coordinate comparison |
| --- | ---: | ---: | ---: | --- |
| BG001, modeled 4-in scenario | 3.25 / 3.00 in (82.550 / 76.200 mm) | 78.7908–86.0044 | 3.94 in (100.076 mm) | `a − LG,max = −3.7592 mm`; enclosure condition fails. Not proof the current 4-in item is unfit: actual `LG` may be smaller. `L_min` exceeds the existing 89.8144-mm tip target by 10.2616 mm. |
| BG001, conditional 3.75-in scenario | 3.00 / 2.75 in (76.200 / 69.850 mm) | 78.7908–86.0044 | 3.69 in (93.726 mm) | `a − LG,max = +2.5908 mm`; `L_min − b = 7.7216 mm`. `LB,min` clears the packet's 68.707-mm comparator by 1.143 mm, and `L_min` clears its 89.8144-mm tip target by 3.9116 mm. This is a table-supported specification alternative only, not a selected product or approved length change. |
| BG045, conditional 8-in scenario | 7.00 / 6.75 in (177.800 / 171.450 mm) | 179.6908–186.9044 | 7.82 in (198.628 mm) | `a − LG,max = +1.8908 mm`; `L_min − b = 11.7236 mm`. Enclosure arithmetic passes only. |
| BG003, conditional 9.5-in scenario | 8.50 / 8.25 in (215.900 / 209.550 mm) | 218.4908–225.7044 | 9.32 in (236.728 mm) | `a − LG,max = +2.5908 mm`; `L_min − b = 11.0236 mm`. Enclosure arithmetic passes only; Ro-Brand HC5127's listing does not claim part-specific B18.2.1 conformity. |

The 3.75-in BG001 figures come from the 1/4-in Table 12 row at nominal 3.75
in and Table 13's −0.06-in tolerance for 1/4–3/8-in screws over 2.5 through
4 in. The 4-, 8-, and 9.5-in rows are the corresponding nominal length
scenarios. Every standard row is conditional on the exact screw conforming to
that standard; none is a received-part finding. BG045's Lawson lead identifies
B18.2.1 dimensions, while the BG003 Ro-Brand lead does not make that claim.

The earlier inference that the nut intervals were on a “GO-gageable nut
travel path” was mistaken. Neither a positive `a − LG,max` nor the overall
length margin supplies the gage working length, the male full-form thread
interval, or the nut's active internal-thread interval. Thus no
standard-conforming 2A/2B scenario demonstrated here establishes travel
through the full nut height or a minimum load-bearing engagement length.
Conditional profile arithmetic remains possible without waiting for delivered
inspection, but it needs declared or source-bounded male first/last complete
thread coordinates and nut active-thread/chamfer bounds. A matched-part
inspection could characterize the received pieces, but is not a prerequisite
to that conditional arithmetic.

No contact footprint is inferred. B18.2.1 §4.3 measures cap-screw washer-face
diameter 0.004 in below the bearing plane toward the head; that dimension is
not itself a guaranteed flat contact circle at the bearing plane. No nut
chamfer, bearing-land, or active-thread limit is asserted here from B18.2.2.

## Source provenance

- [ASME B18.2.1-2012 (R2021) official record](https://www.asme.org/codes-standards/find-codes-standards/b18-2-1-square-hex-heavy-hex-askew-head-bolts-hex-heavy-hex-hex-flange-lobed-head-lag-screws); [inspected full-text PDF mirror](https://www.szjlin.com/static/upload/file/20210111/1610336127463997.pdf). Local inspection copy: `/tmp/thread-gage-functional-fit/ASME-B18.2.1-2012-mirror.pdf`, SHA-256 `4c7bcb75223b7e89fc27f132bc44e8b422ba672c97f7803259a24fab6bd99ba0` (same bytes/hash recorded in the [existing source correction](../../bolt-dimension-source-correction.md)). Definitions and class provisions: §§1.5–1.6 and 2.4–2.5; `LG`/`LB` and `LT` provisions: §4.7 and Table 6; conditional limits: Tables 12–13, with Table 13 printed p. 23. This is a third-party-hosted copy of the named standard, not an ASME-hosted download.
- [ASME B18.2.2-2022 official record](https://www.asme.org/codes-standards/find-codes-standards/b18-2-2-nuts-general-applications-machine-screw-nuts-hex-square-hex-flange-coupling-nuts); inspected [third-party text/PDF mirror](https://ul.isodoc.my/asme/ASME%20B18.2.2%202022.pdf). No local copy/path or SHA-256 is pinned in this working set; no B18.2.2 chamfer/contact dimensions are asserted in this note. The regular-hex nut outer-height envelope is carried forward only as a declared input from the [hardware-material packet](../hardware-material-specification-2026-09-30/README.md), not revalidated here.
- Project geometry and comparators: the [hardware-material packet README](../hardware-material-specification-2026-09-30/README.md), [fastener source screen](../hardware-material-specification-2026-09-30/fasteners.md), and [per-axis requirements](../hardware-material-specification-2026-09-30/requirements.md). The B18.2.1 correction and prior boundary screen are [here](../../bolt-dimension-source-correction.md) and [here](../../current-bolt-thread-boundary-screen-2026-09-27.md).
