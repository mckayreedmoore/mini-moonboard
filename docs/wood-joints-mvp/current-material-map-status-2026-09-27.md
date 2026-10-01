# Current WJ24 material-map status — 2026-09-27

**Status:** source-map coverage addendum for the reviewed
`led-clearance-2x6-runner-seated-blocks-v1` revision. This note records the
later material-map artifacts without changing the pinned
[`current-material-scenarios.md`](current-material-scenarios.md), either map,
or the frozen full-frame manifest. It is not a mechanics input or a physical
stock record.

## Current map coverage

| Current body group | Source-bound coverage | Still unresolved |
| --- | --- | --- |
| 20 frame timbers | The attempt01 longitudinal map binds all 20 current timber IDs to exact STEP bodies, source `X/T/N` frames and grain proposals. The separately reviewed transverse scenario map adds two right-handed `L/R/T` cases per member, preserving each grain vector. | Board-specific growth-ring orientation and selection of a material case; solver element assignment; delivered species, grade, treatment, moisture and receiving condition. No material properties are assigned. |
| 24 connector blocks | The attempt02 block map binds all 24 current IDs to conditional source frames, grain proposals, and two right-handed transverse `R/T` cases per block. The inner-frame `+Z` choice remains the less directly documented scenario. | Which transverse case matches each physical board; delivered stock identity and condition. These are analysis alternatives, not a physical bound or selected material assignment. |
| 6 plywood panels | The full-frame manifest binds the six exact panel solids in the 50-member bundle. | Layup, principal material axes, properties, and received panel identity are not mapped. No panel orthotropy is inferred from panel outline or CAD geometry. |
| Candidate steel hardware | The reviewed steel role map binds all 460 modeled roles on 92 candidate axes to the declared generic isotropic elastic proposal and nine sensitivity cases. Head and shaft share a physical-bolt identity while remaining separate source roles. | Solver-body/element assignment, physical product identity and delivered steel properties remain unresolved. The 60 roles on the 12 retained stacks are separately inventoried and unassigned; their current-candidate recheck remains required. |

The preserved attempt03 full-frame manifest binds both original timber-map artifacts to the 50
finished solids (20 timber members, 6 panels, and 24 blocks), the source-bound
gravity inventory, and six applied-load cases. The manifest explicitly keeps
`inputs_ready=false`; this status note does not change that gate.
The newer [frame transverse scenarios][transverse-map] and
[steel role map][steel-map] are separate source-bound inputs, with algebra
and identity reviews complete. The new [attempt04 manifest][manifest04] binds
these additions while preserving attempt03. Its parent review and source
verification pass; full-frame readiness remains false.

## Interpretation limits

The frame and block records describe conditional model orientations only. They
do not identify an inspected board, certify a grade, assign a post-rip grade,
or establish moisture, treatment, or receiving condition. In particular, the
four proposed section-ripped 4×6 blocks retain the separate grade disposition
in the [current timber grade note][grade]; no original grade or design value
transfers across those rips.

Generic elastic values and mapped wood directions do not establish resistance,
bolt fit, contact behavior, demands, capacity, or acceptance. No current
candidate or release gate is closed by this map-coverage update.

## Frozen source references

The original material-scenario file is a hashed dependency of multiple frozen
artifacts, including full-frame manifest attempt03. Its SHA-256 remains
`dd76354c0fa68a01a336cef22fe1cf854baaaf1ceda22dd11ceb881a274bb3c4`; this
addendum is separate so those frozen inputs remain unchanged.

| Source | SHA-256 |
| --- | --- |
| [Current material scenarios](current-material-scenarios.md) | `dd76354c0fa68a01a336cef22fe1cf854baaaf1ceda22dd11ceb881a274bb3c4` |
| [Frame timber map README][frame-map] | `4c465d77dfd069f5fa69fbcc729ebe18cee42ece6c812d0c3ba059fd045d8e1d` |
| [Frame timber map JSON][frame-map-json] | `f867b4926ed23c9f356005c134778e138c8b1230547f0b69be7c3f9bc2a42409` |
| [Block material map README][block-map] | `dd25a3c19f88238cfff4697c34b1cc00916f5b411636366f5d0fb26951e943d2` |
| [Block material map JSON][block-map-json] | `8705b8f100a2d3355c236fc19e6798bb7ad4862ba2d51826cf63a88db1285480` |
| [Full-frame manifest attempt03 README][manifest] | `98455c87f1961517a4a6747b60ff1c27d6b2e05612dc53051f6f31bad5b4961b` |
| [Full-frame manifest attempt03 JSON][manifest-json] | `2f5eed3e4fa01e62e776d8fc0e4fae12182f86e1d84c63c956dbe7b44fbb5896` |
| [Current timber grade disposition][grade] | `7266a00f72dbe46ac6917cfc7ee3588f85ca5d42d9daf4a916ff6fa529a873b0` |
| [Frame transverse scenario JSON][transverse-json] | `8c7646dcbce4ad94c99a422a3e93aaee87644faf56c125fc09c5176dd4a2d714` |
| [Candidate steel role-map JSON][steel-json] | `13ed1afcfbc9343207b9e8eb498f8fb3762ec2cdbe0719963f26037cc77027cc` |
| [Full-frame manifest attempt04 JSON][manifest04-json] | `9e682e28c3d4c3c0594863f82c6b74d19dee2700f3856d34e1a26f69082e4f11` |

[frame-map]: hypotheses/evaluation-resume-2026-09-24/current-frame-timber-material-frame-map-attempt01/README.md
[frame-map-json]: hypotheses/evaluation-resume-2026-09-24/current-frame-timber-material-frame-map-attempt01/current-frame-timber-material-frame-map.json
[block-map]: hypotheses/evaluation-resume-2026-09-24/current-block-material-frame-map-attempt02/README.md
[block-map-json]: hypotheses/evaluation-resume-2026-09-24/current-block-material-frame-map-attempt02/material-frame-map.json
[manifest]: hypotheses/evaluation-resume-2026-09-24/current-full-frame-input-manifest-attempt03/README.md
[manifest-json]: hypotheses/evaluation-resume-2026-09-24/current-full-frame-input-manifest-attempt03/current-full-frame-input-manifest.json
[grade]: hypotheses/evaluation-resume-2026-09-24/current-timber-grade-disposition-attempt01/README.md
[transverse-map]: hypotheses/evaluation-resume-2026-09-24/current-frame-timber-transverse-scenarios-attempt01/README.md
[transverse-json]: hypotheses/evaluation-resume-2026-09-24/current-frame-timber-transverse-scenarios-attempt01/transverse-scenarios.json
[steel-map]: hypotheses/evaluation-resume-2026-09-24/current-steel-elastic-role-map-attempt01/README.md
[steel-json]: hypotheses/evaluation-resume-2026-09-24/current-steel-elastic-role-map-attempt01/steel-elastic-role-map.json

[manifest04]: hypotheses/evaluation-resume-2026-09-24/current-full-frame-input-manifest-attempt04/README.md
[manifest04-json]: hypotheses/evaluation-resume-2026-09-24/current-full-frame-input-manifest-attempt04/current-full-frame-input-manifest.json
