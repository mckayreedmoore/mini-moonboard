# Finished-edge review: bottom outer left bolt axes

## Finding

The finished STEP solids have rectangular exterior cross-sections at these four axis stations, with two qualifications that a stock-box-only check would miss. `base_side_left` has a beveled near end, so its actual g− edge is closer than the proposed stock-envelope coordinate implies. `bottom_outer_left_cleat` has two perpendicular bolt-hole families whose modeled cylindrical cuts leave a 9.0 mm ligament. Cross-section rays also enter the paired 7.5 mm bore voids. The rail carries repeated service passages along its length, with the nearest passage intersecting a g+ ray 86.129 mm from the target center.

This is a source-bound geometry review only. A face or cylinder match is not an observed lumber feature, permitted cut, fastening instruction, resistance check, or joint acceptance.

## Source binding and method

The reviewed source candidate/revision is `compact-floor-flush-wood-joints-development` / `led-clearance-2x6-runner-seated-blocks-v1`, from `current-full-frame-input-manifest-attempt04`. The four axes are `bottom_outer/clip_horizontal_bottom_left_1/{rail,side}_{1,2}`. The [finished-surface register](../current-finished-feature-register-2026-10-01/surfaces.md) and [axis correspondence](../current-finished-feature-register-2026-10-01/axis-features.md) bind their receiver memberships to finite trimmed cylindrical faces in the saved finished STEP solids. The axis join is explicitly metadata-only and does not establish an installed or usable hole.

I verified the pinned `axis-features.json`, `surfaces.json`, and each of the three STEP byte hashes below, then imported those existing STEP files read-only. Each import was a valid single solid. I checked 96 rays: for each of the eight receiver memberships, at the matched cylinder interval's two ends inset by 0.01 mm and its midpoint, I queried both signs of each of the two receiver-frame directions perpendicular to the bolt axis. Material intervals retain intervening voids. The face register's trim loops and exact planar equations were used to identify stock faces, bevels, and cylindrical openings. The ray samples are discrete stations; they do not certify all possible hardware bearing footprints or physical contact.

## Receiver edges and cuts

All dimensions are millimetres in the proposed receiver g/q/r frame. “− / +” distances below run from the modeled bolt-axis center to the actual finished outer boundary in the indicated cross-section direction. The matched receiver cylinder radius is 3.75 mm in every row; the source occupied bolt-axis diameter is 6.35 mm. The STEP cylinder describes modeled cut geometry, not a drill-bit or delivered-hole specification.

| Axis and receiver | Matched face | Cross-section edge distances and findings |
| --- | --- | --- |
| `rail_1`, `base_rail_bottom_left` | `facet013` | At g=45.45, r=53.35, the g-axis ray reaches the g− end plane `facet002` at 45.45 and the g+ end plane `facet018` at 995.80. The r−/r+ outer planes `facet003` / `facet001` are 53.35 / 86.35 away. The paired rail bore is 33.0 mm away in r; its 7.5 mm modeled diameter leaves 25.5 mm between the two parallel bore surfaces. |
| `rail_2`, `base_rail_bottom_left` | `facet017` | At g=45.45, r=86.35, the g distances are again 45.45 / 995.80; the r−/r+ distances are 86.35 / 53.35. The paired rail bore is the same 33.0 mm spacing. |
| `side_1`, `base_side_left` | `facet013` | At g=284.368, q=69.85, the q−/q+ planes `facet015` / `facet018` are 69.85 / 69.85 away. The actual g− terminal is bevel plane `facet035` at 256.715 mm; g+ terminal plane `facet016` is 2255.400 mm away. The paired side bore is 33.0 mm away in g, leaving 25.5 mm between parallel modeled bore surfaces. |
| `side_2`, `base_side_left` | `facet012` | At g=317.368, q=69.85, the q−/q+ distances remain 69.85 / 69.85. The actual g− bevel and g+ terminal distances are 289.715 / 2222.400 mm. The paired side bore is again 33.0 mm away. |
| `rail_1`, `bottom_outer_left_cleat` | `facet009` | At g=43.35, r=43.45, g−/g+ distances are 43.35 / 76.35 and r−/r+ are 43.45 / 45.45. |
| `rail_2`, `bottom_outer_left_cleat` | `facet010` | At g=76.35, r=43.45, g−/g+ distances are 76.35 / 43.35 and r−/r+ are 43.45 / 45.45. |
| `side_1`, `bottom_outer_left_cleat` | `facet006` | At g=59.85, q=28.00, the g−/g+ distances are 59.85 / 59.85; q−/q+ are 28.00 / 60.90. |
| `side_2`, `bottom_outer_left_cleat` | `facet007` | At g=59.85, q=61.00, the g−/g+ distances are 59.85 / 59.85; q−/q+ are 61.00 / 27.90. |

The rail receiver is an otherwise rectangular 1041.25 × 38.10 × 139.70 solid at the target station. Its six outer planes are `facet001`, `facet002`, `facet003`, `facet008`, `facet018`, and `facet019`; the q-facing planes `facet008` and `facet019` contain the through-hole loops. Along g+, each target ray first enters the nearest 38.10 mm diameter service passage at a distance of 86.129 mm; the ray void is 19.042 mm wide at the sampled r offsets. Four more service passages repeat at 200 mm spacing. A separate 3.75 mm-radius starting-bolt cut near the far end also interrupts the ray. The underside plane `facet003` has two 2.0701 mm-radius cylinders at g=295.225 and 695.225; the axis register identifies them as the two moved panel/kicker screw memberships, well away from the target g=45.45 station. They terminate at internal planar caps `facet005` and `facet007` after 45.244 mm. These are circular openings, not a local slot or chamfer at the target bolts. The q-facing planar perimeter remains stock-rectangular at the sampled target stations.

`base_side_left` also has two nonstock end bevel faces, `facet017` and `facet035`. They occupy the g<86.264 end region; the target centers at g=284.368 and 317.368 are beyond that region. At q=69.85 the actual g− rays meet `facet035` where g=27.653, which explains why actual edge distances are 27.653 mm shorter than the g coordinate from the proposed stock origin. The finished-solid g+ terminal is `facet016` at g=2539.768, while the stock-envelope metadata lists 2570.726 mm; its far-edge distances must therefore come from the finished STEP, not that metadata length. The broad side faces have many circular through-hole trims. The only additional opening crossed by these g+ sample rays is a remote radius-7.144 mm bore at g=2005.310, producing a 7.228 mm void at distances 1717.329–1724.557 mm for `side_1` and 1684.329–1691.557 mm for `side_2`. No such cut lies near either target station.

The cleat exterior consists of six planar stock faces (`facet001`, `facet002`, `facet003`, `facet004`, `facet005`, `facet008`), with circular bore openings and no additional planar notch or relief. Its two rail bores run through q at (g,r)=(43.35,43.45) and (76.35,43.45); the two side bores run through r at (g,q)=(59.85,28.00) and (59.85,61.00). Each rail/side pairing has finite-axis closest points inside the registered 0.1–89.0 mm cylindrical intervals: the axes are 16.50 mm apart in g and the radii are 3.75 mm each. The minimum modeled wall between each perpendicular bore pair is therefore 9.00 mm. At the sampled side-bore midpoint, both g rays show the neighboring rail bore as a 7.228 mm void spanning 12.886–20.114 mm from the side-bore center. This cut interaction is absent from a rectangular-stock edge-distance calculation and must remain explicit in any later section check.

## Exact inputs and limits

| Input | SHA-256 |
| --- | --- |
| `current-finished-feature-register-2026-10-01/axis-features.json` | `bebb4274cdecfb6ad0b0f26850d85a16570c245ea9f7d478c0b05c12b4513e19` |
| `current-finished-feature-register-2026-10-01/surfaces.json` | `33fff67eee4bc4e96ccef5703f6eebd0d4e004541c6114a4b1da4a5332b2f6eb` |
| `current-finished-feature-register-2026-10-01/axis-source-pins.json` | `7a501047c003174c15461ae12e3cd47af4e4bf59b1d40d3c8e5b76d8e1904d34` |
| `current-finished-feature-register-2026-10-01/source-pins.json` | `0e8cb56407f14e93d7ab95741115d4355a954eb845ae503365ba1da1149bd9cd` |
| `current-finished-feature-register-2026-10-01/axis_features.py` | `e9787320589db65f1443b2c40607ed347cd5c4e8d5c8a2b9be73a5619275104f` |
| `current-finished-feature-register-2026-10-01/surfaces.py` | `a58e8f76b0d308352c734b6eab6bdea8c3adb75ab1c538e0905997d0232bab4f` |
| `mini_moonboard/connection_geometry.py` (strict-interior material intervals) | `f729bc64e7ea7fb9df9308411df07e02f98fc309efcf26038809a9e7bd4bc4a4` |
| `base_rail_bottom_left.step` | `724d46fa7902a949b79b0fd6132c5e57c580be80aad7d059c29e04494ff79923` |
| `base_side_left.step` | `237c3fa6aa0b52c39124580810d048e38919b99b9a1fb5db5a2423e7eda62fdf` |
| `bottom_outer_left_cleat.step` | `28d1b5fee748c38e30e3d2618c8377cfe374c7ccd0b520736c25841720824438` |

The feature register reports CadQuery 2.8.0, OCP module 7.9.3.1 and OCP package 7.9.3.1.1. Its proposed stock frames are analysis datums, not delivered-lumber measurements. The 96 rays and exact BREP trims establish only the sampled analytical geometry of this left-side assembly. They do not establish physical lumber, a bearing footprint, cut authorization, wood resistance, complete joint behavior, fabrication release, or climbing acceptance.
