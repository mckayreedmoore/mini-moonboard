# Current retained-frame-bolt access screen

The current WJ24 model flags a concrete modeled overlap: all four lumber-leg
bolt withdrawal paths intersect wire solids. The four front-rail and four
rear-rail paths are clear in the screened source-BRep envelopes. Nut and
nut-washer translation envelopes are clear for all twelve stacks after the
assumed thread disengagement. Wrench results remain provisional proxy checks;
they do not establish tool access or a real obstruction.

The checked revision is `led-clearance-2x6-runner-seated-blocks-v1`, reviewed
commit `b1e8707d`. The exact twelve targets and source receiver order are:

| Stack IDs | Ordered source receivers | Head-to-nut axis | Nominal length / grip | Derived head-side travel |
| --- | --- | --- | --- | --- |
| `lumber_leg_bolt_left_1`, `lumber_leg_bolt_left_2` | `base_side_left` → `lumber_leg_left` | −X | 203.2 / 177.8 mm | 200.025 mm |
| `lumber_leg_bolt_right_1`, `lumber_leg_bolt_right_2` | `base_side_right` → `lumber_leg_right` | +X | 203.2 / 177.8 mm | 200.025 mm |
| `rail_front_bolt_left_1`, `rail_front_bolt_left_2` | `base_post_outer_left` → `base_floor_left` | −X | 101.6 / 76.2 mm | 99.568 mm |
| `rail_front_bolt_right_1`, `rail_front_bolt_right_2` | `base_post_outer_right` → `base_floor_right` | +X | 101.6 / 76.2 mm | 99.568 mm |
| `rail_rear_bolt_left_1`, `rail_rear_bolt_left_2` | `base_floor_left` → `lumber_leg_left` | −X | 114.3 / 88.9 mm | 112.268 mm |
| `rail_rear_bolt_right_1`, `rail_rear_bolt_right_2` | `base_floor_right` → `lumber_leg_right` | +X | 114.3 / 88.9 mm | 112.268 mm |

All eight receiver IDs map to the current finished solids without remapping.
Source `protected` role aliases are fingerprint-matched to five installed
components per bolt: shaft, head washer, nut washer, head, and nut. The sixth
shape on each source stack is the nonphysical `source_occupied_axis` display
proxy. The screen drops those 12 proxies and records their IDs and geometry
separately. It keeps all 60 physical retained-bolt components, all 92 candidate
stacks stationary, and all 142 physical T-nuts stationary. The source contract
classifies 36 frame-tool/withdrawal envelopes and 142 hold-hole/provisional
rear-projection envelopes as access-only; attempt03 records and excludes those
178 envelopes from installed-part collision checks. The 142 corresponding
T-nuts remain obstacles. The resulting live obstacle map contains 1,041
shapes.

The exact translation checks report these modeled intersections:

| Operation | Result in the screened source geometry |
| --- | --- |
| Head, head washer, and shaft withdrawn together | 24 of 36 component sweeps clear. All three component sweeps intersect `protected/wires/wire_010_A10_A11` for both left lumber-leg bolts; all three intersect `protected/wires/wire_130_K10_K11` for both right lumber-leg bolts. Each of the other eight stacks has three clear component sweeps. |
| Nut removal and reverse translation | 12 of 12 clear in each direction after full thread disengagement is assumed. Derived axial travel is 19.05 mm on the leg bolts and 21.336 mm on rail bolts. |
| Nut-washer removal and reverse translation | 12 of 12 clear in each direction after nut removal is assumed. Derived travel is 22.225 mm on the leg bolts and 23.368 mm on rail bolts. |

The head-side travel comes from current finished-receiver vertex extrema and
the modeled shaft envelope. It has zero terminal allowance and no added
clearance. The translation methods are `exact_coaxial_cylinder_translation_sweep`
for the shaft, `exact_source_brep_cylinder_translation_sweep` for the head,
and `exact_source_brep_annular_cylinder_translation_sweep` for washer and nut
solids. “Exact” describes those modeled source BReps, not delivered hardware.
Thread motion, nut unthreading, support transfer, and capture are not screened.

Wrench checks use a provisional FACOM `facom_34_7_16` profile (22 mm wide,
3 mm thick, 100 mm overall), with synthetic 15° and 75° headings. It is not a
selected or verified tool; open-end jaw engagement and hand clearance are not
represented. Across 192 sampled proxy envelopes per end, the head-side proxy
is clear in 91 and overlaps modeled geometry in 101; the nut-side proxy is
clear in 140 and overlaps in 52. Head-side hits are `wood/kicker_left`,
`wood/kicker_right`, `wood/main_upper_left`, `wood/main_upper_right`, and the
head shapes of `lumber_leg_bolt_left_1`, `lumber_leg_bolt_left_2`,
`lumber_leg_bolt_right_1`, `lumber_leg_bolt_right_2`,
`rail_front_bolt_left_2`, `rail_front_bolt_right_1`,
`rail_front_bolt_right_2`, `rail_rear_bolt_left_2`,
`rail_rear_bolt_right_1`, and `rail_rear_bolt_right_2`. Nut-side hits are nut
and shaft shapes of `lumber_leg_bolt_left_1`, `lumber_leg_bolt_left_2`,
`lumber_leg_bolt_right_1`, `lumber_leg_bolt_right_2`,
`rail_front_bolt_left_1`, `rail_front_bolt_left_2`,
`rail_front_bolt_right_2`, `rail_rear_bolt_left_1`,
`rail_rear_bolt_right_1`, and `rail_rear_bolt_right_2`. These are
proxy-envelope intersections, not evidence that a real wrench cannot be used.
The 30° rotation intervals are conservative AABB enclosures, not exact wrench
sweeps. Clear proxy samples also do not prove access.

Attempt02 is preserved as an invalid collision screen: it left the 36 temporary
frame-tool/withdrawal envelopes and 142 hold projection envelopes in the
installed-obstacle map. Its reported overlaps therefore cannot be read as
blockage. Attempt03 corrects this classification; see the
[attempt02 record](hypotheses/evaluation-resume-2026-09-24/retained-access-attempt02/README.md)
and [corrected attempt03 run](hypotheses/evaluation-resume-2026-09-24/retained-access-attempt03/README.md).

The screened-subset sequence graph has no edges or cycles, but is explicitly
incomplete for all 92 axes and all build states. The result is not a complete
joint assembly/disassembly sequence, physical access check, hardware fit check,
mechanics result, or fabrication release. The bounded JSON report is
[access.json](hypotheses/evaluation-resume-2026-09-24/retained-access-attempt03/access.json).

Attempt03 completed in 9.662 s with source files unchanged and no native solve.
Its report SHA-256 is
`fffa0027926a57583cc13ffbcef552fc8e5f8da96964d50c64ef63ffd4ce4c97`; the
canonical geometry-snapshot SHA-256 is
`50d3d65c6f5eeddbd8df8bf068c7f338754c831c7cc49b25ccc4f4a878902a7a`, and the
source-inventory SHA-256 is
`07af4c3eb642cf3887595fe4415eb65404cdcf74d66c5c7bb182847ef21c2d78`. The
corrected producer and focused-test hashes are recorded in attempt03's
`execution.json`.
