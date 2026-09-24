# WJ-05 upper-cleat global-Z grain alternative

**Status: deferred analytical comparison only.** This orientation is not
selected or implemented. It does not change the current WJ-05 geometry, source
inventory, 66 fixed panel/kicker axes, or 12 starting frame bolts. This note
adds no receiving, inspection, or release requirement.

## Geometry screen

Use current upper-cleat outline inputs from the
[center-node probe](../../../scripts/wood_joint_wj05_center_node_probe.py) and
[source inventory](../source-inventory.json):
`X = 89.05…177.95 mm`, `N = 50.8…139.7 mm`, grain length `82 mm`,
`θ = 50°`, datum `(Y₀, Z₀) = (−41.497331, 277 mm)`. Let
`s = sin θ`, `c = cos θ`. The current outline has bounding dimensions:

```text
X = 88.9 mm
Y = 82c + (139.7 − 50.8)/s = 168.76 mm
Z = 82s = 62.815644 mm
```

Hypothetical grain vector is `g_c = (0, 0, 1)`. Existing principal-bolt
axes are `±X`, so `a·g_c = 0`; header-bolt axes are `+Z`, so `a·g_c = 1`.
Source principal grain is `T = (0,c,s)` and header grain is `+X`; each
corresponding bolt axis is perpendicular to those host grains. This resolves
bolt-axis orientation categories only; lateral load-to-grain directions still
depend on signed demands.

For proposed principal bolts at `N = 78.75, 111.75 mm`, common
`Z = Z₀ + 82s/2 = 308.407822 mm`, transform coordinates by:

```text
T = (Z − Z₀ − cN)/s
Y = Y₀ + (c(Z − Z₀) − N)/s
```

This gives centers `(T,N,Y) ≈ (−25.079, 78.75, −117.944)` and
`(−52.769, 111.75, −161.022) mm`. Their pitch is
`ΔY = 33/s = 43.078441 mm`. At this Z, cleat Y edges are
`−197.508438` and `−81.457730 mm`, leaving `36.486134 mm` nearest edge
distance at each bolt. In the source principal member, whose N bounds are
`0…139.7 mm`, nearest N edge distance is `139.7 − 111.75 = 27.95 mm`.
The bolt-row vector projects to `27.690288 mm` along host T and `33 mm`
across T; it is oblique to the host grain and does not establish a simple
parallel-row tear-out case.

For header bolts at X=`116, 151 mm`, Y=`−139.4 mm`, the pair pitch remains
`35 mm`. Cleat minimum X-edge distance is `26.95 mm`; minimum Y-edge
distance across the end faces is about `31.58 mm`.

With nominal `D = 6.35 mm` only, principal cleat grain-end distance is
`82s/2 = 31.407822 mm = 4.946D`; cleat cross-grain Y edge distance is
`5.746D`; principal-host N edge distance is `4.402D`; and header-axis
cleat X-edge distance is `4.244D`. These are geometry ratios, not acceptance.
Under NDS Table 12.5.1A, 31.408 mm is between 4D and 7D for softwood tension
toward an end; actual signed loading and member category control any geometry
factor. The tight nominal edge margins do not include delivered-part or cut
tolerances.

The proposed cleat spans Z=`277…339.815644 mm`, so header bolts would enter
its bottom end grain and run parallel to its grain. The cleat provides about
62.816 mm bearing length along those bolts versus 38.1 mm in the header, so
the cleat is a plausible main member; confirm member-role applicability for a
later connection model. Its bottom end-grain seat overlaps the header over
about 67.9 mm of the 116.05 mm Y span. That contact and the short cleat's
net-section/member actions need separate evaluation. The top nut washer
would compress parallel to cleat grain; the existing perpendicular-to-grain
washer reference does not cover that face.

## Conditional NDS method boundary

NDS-2024 §12.3.3.4 states that for dowel-type fasteners with `D ≥ 1/4 in`
inserted into the end grain of the main member with axis parallel to fibers,
`Fₑ⊥` is used for that member's dowel-bearing input `Fₑm`. Section 12.5.2.2
also applies end-grain factor `Ceg = 0.67` to reference lateral value `Z`.
Thus this orientation offers a defined end-grain route for the header bolts,
not a no-penalty side-grain result. The 1/4-in nominal bolt is exactly at
the §12.3.3.4 threshold. The repository's `Dr ≈ 0.189 in` 1/4-20 thread-root
case is a sensitivity, not a delivered measurement; NDS §§12.3.7.1–12.3.7.2
scope the effective-diameter rule to Tables 12.3.1A/B. Do not silently
substitute `Dr` or nominal `D` into §12.3.3.4's threshold without a supported
interpretation and actual fastener basis. See the
[bolt-resistance basis](../bolt-resistance-basis.md).

The outline fits only as a stock-envelope hypothesis: any source blank would
need at least `88.9 × 168.76 mm` cross-section and `62.816 mm` length along
grain. Available solid stock, grain orientation, species/grade, defects, and
applicability of lumber values to this short, angled cut are unverified. No
wood or bolt capacity, load distribution, washer resistance, complete-joint
result, drilling instruction, or receiving criterion follows from this
comparison. Existing actions, material evidence, and full geometry checks
remain governed by the active WJ-05 work.

## Sources

- [AWC NDS-2024 Chapter 12, Dowel-Type Fasteners](https://awc.org/wp-content/uploads/2026/08/AWC_NDS2024_withCommentary_20250328_WebsiteChapter-12-%E2%80%93-Dowel-type-fasteners.pdf)
- [AWC NDS-2024 record](https://awc.org/resources/2024-nds/)
- [WJ-05 bolt and washer resistance basis](../bolt-resistance-basis.md)
- [WJ-05 wood limit-state basis](../wood-limit-state-basis.md)
