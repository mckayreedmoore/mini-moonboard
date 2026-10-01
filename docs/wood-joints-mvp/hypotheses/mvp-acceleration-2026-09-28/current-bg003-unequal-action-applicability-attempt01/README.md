# BG003 unequal-action applicability screen — attempt01

**Result:** no current NDS-2024 complete lateral-yield method was identified
for the actual two-plane, unequal and non-collinear actions at BG003. The
packet reproduces those actions and checks only four conditional outer-member
Mode Is components. Their largest ratio is 0.2754 under the stated material
and bolt scenarios. This is not a full-connection DCR, capacity, pass, or
acceptance.

## Applicability finding

The current AWC NDS-2024 Chapter 12 says §12.3.1 reference lateral values
cover single-shear and **symmetric** double-shear connections. Section
12.3.5.4 addresses unequal side-member *bearing lengths* by using the shorter
length on both sides; that geometric rule does not supply a way to combine
unequal, differently directed plane actions. Section 12.3.8 is the separate
four-or-more-member procedure and does not apply to BG003's three members.
The exact 2024 source is pinned in the earlier current lateral-bolt method
packet at SHA-256
`5fc837523ff10acc097a162718700a9b4ba64e627d2b0023439146d42fe4ee2a`; see the
[official AWC NDS-2024 page](https://awc.org/resources/2024-nds/) and the
[official Chapter 12 PDF](https://awc.org/wp-content/uploads/2026/08/AWC_NDS2024_withCommentary_20250328_WebsiteChapter-12-%E2%80%93-Dowel-type-fasteners.pdf).

As historical context only, the AWC 2018 NDS had a §12.3.8 provision titled
asymmetric three-member double shear. Its official commentary says the method
assumes equivalent load to each side member and may need more complex analysis
for other distributions. This confirms why that legacy symmetric shortcut
cannot represent BG003's current force split; the 2018 text is not substituted
for the 2024 edition. Sources: [2018 Chapter 12](https://awc.org/wp-content/uploads/2021/10/AWC_NDS2018-withCommentary_20210928_AWCWebsite_Chapter12.pdf),
[2018 Commentary C12.3.8](https://awc.org/wp-content/uploads/2021/10/AWC_NDS2018-withCommentary_20200827_AWCWebsite_Commentary.pdf).

## Source-bound force screen

The source is the accepted final full-load a12-rear corner report, SHA-256
`812a62fa3cd96a8983649c84a8c78a8d176d639465c887b11d1827a3f8f1ee17`. The
report's per-plane force vectors are carried in global coordinates; they are
not inferred from whole-body equilibrium. BG003 has two bolts, each with two
adjacent lateral planes:

| Bolt | Spine-plane action on spine (N) | Block-plane action on inner block (N) | Resultant ratio | Angle between actions |
| --- | --- | --- | ---: | ---: |
| side_1 | (0, −292.4238, 385.6081), 483.948 N | (0, 0.9184, 65.9067), 65.913 N | 7.3422 | 37.973° |
| side_2 | (0, 230.4513, −64.2122), 239.230 N | (0, −20.7149, 84.4807), 86.983 N | 2.7503 | 119.347° |

Thus neither bolt has equal, collinear outer actions. In particular, the
second bolt's two outer actions are more than 90° apart. The middle member
`base_side_left` receives both opposite plane actions. Its net lateral force
is 537.439 N for side_1 and 210.714 N for side_2; the pinned report also
retains the associated moments at each bolt datum. Those coupled middle-member
actions and the dowel's force/moment transfer between separated planes are
not resolved by the component calculation below.

## Conditional necessary component comparison

The only resistance numbers here are separate outer-receiver embedment-mode
components, using the NDS single-shear Mode Is expression

```text
Z_Is = Fe,s(theta_s) D ell_s / (4 Ktheta)
Ktheta = 1 + 0.25 theta_max / 90
```

where `theta_max` is the greater proposed load-to-grain angle in that local
two-member plane. The screen uses the reviewed DF-L dowel-bearing helper for
`Fe,s`, the proposed outer and middle grain vectors from the pinned material
maps, the modeled 1/4-in diameter, and an effective side length of 1.5 in for
both outer members. Using 1.5 in for the modeled 3.5-in inner block is a
deliberately conservative component input consistent with the shorter-side
rule; it is not a newly asserted physical bearing length. Only this Mode Is
term is reported. No independent plane capacities are added.

| Bolt plane | Side member | Demand | Conditional Mode Is reference | Demand / Mode Is |
| --- | --- | ---: | ---: | ---: |
| side_1 / plane-37 | spine | 483.948 N (108.796 lbf) | 395.047 lbf | 0.2754 |
| side_1 / plane-38 | inner block | 65.913 N (14.818 lbf) | 473.421 lbf | 0.0313 |
| side_2 / plane-39 | spine | 239.230 N (53.781 lbf) | 350.903 lbf | 0.1533 |
| side_2 / plane-40 | inner block | 86.983 N (19.555 lbf) | 450.170 lbf | 0.0434 |

This is a necessary local embedment-mode component screen only. Values below
one do not establish adequate whole-joint resistance. No central-member
simultaneous bearing/moment interaction, bolt bending across both planes,
bolt tension or tension/lateral interaction, two-bolt group distribution,
splitting/net-section/row-shear/tear-out, NDS adjustments, delivered hardware,
or received-stock properties are resolved. The conditional inputs retain the
prior scenario of solid DF-L lumber `G=0.50`, smooth full-body `D=0.25 in`,
and proposed grain; none is verified delivered-material evidence.

The current consolidated AWC errata was checked at SHA-256
`b3f4f8b3b2e2ffa5eb618de9e1182614c329d9e4a135096667364dc9a8e473c0`
([official errata PDF](https://awc.org/wp-content/uploads/2026/03/2024-NDS-Errata-and-Addenda-03.23.26.pdf)).
Its page 6 correction concerns the `KD` branch for `0.17 < D < 0.25 in`;
this component uses exactly `D=0.25 in`, so Table 12.3.1B's `4 Ktheta` branch
applies and the `KD` correction does not change the reported Mode Is values.

## Reproduction and limits

Run from the repository root:

```sh
uv run --no-sync python3 docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-bg003-unequal-action-applicability-attempt01/screen.py
```

The script verifies the demand report, earlier symmetric reference scenario,
grain maps, and method-helper hashes before rewriting [`screen.json`](screen.json).
It does not run a native solver, alter geometry or a frozen input, calculate a
complete BG003 capacity, qualify the bolt group, or accept the joint. An
applicable coupled three-member resistance method remains the exact open
method dependency before the BG003 lateral demand can be compared to a full
joint resistance.
