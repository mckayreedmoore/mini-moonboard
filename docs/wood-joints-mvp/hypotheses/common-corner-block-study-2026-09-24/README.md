# Common corner-block study, September 24, 2026

The owner subsequently directed implementation of this consolidation. See the
[current viewer checkpoint](../consolidated-blocks-two-inner-bolts-2026-09-24/README.md).
The trial files below retain their original unadopted status and source hashes.

A geometry trial reduces the current 24 blocks from ten distinct finished
shapes/drilling patterns to seven. Fifteen blocks can share one existing
pattern on an unchanged 88.9 × 88.9 × 119.7 mm blank. This is an unadopted
comparison: the current viewer and its ten-design count remain unchanged.

## Closest designs

The template is the existing common middle/outer-top block, represented by
`left_service_inner_lower_cleat`, already used at eight locations.

| Current family | Blocks | Largest hole-axis shift to template | Result |
| --- | ---: | ---: | --- |
| Existing common middle/outer-top pattern | 8 | 0 mm | Already identical after rotation |
| Four bottom rail blocks | 4 | 2.326 mm | Same blank; small hole-pattern changes |
| Two top center blocks | 2 | 2.1 mm | Same blank; only rail-bolt holes move |
| Upper-left inner middle block | 1 | 16.4 mm | Same blank; four axes shift toward the panel |
| **One shared pattern** | **15** | | **Four former designs become one** |

At the bottom blocks, the principal/side axes move 2.05 and 2.15 mm along
wall T. The rail axes move 1 mm across the block and 2.1 mm in opposite wall-N
directions. At the top center pair, only the two rail axes per block move
2.1 mm in opposite wall-N directions. The upper-left inner block's four axes
move 16.4 mm toward the panel. The full [pattern comparison](pattern-comparison.json)
records every actual global translation and the rigid rotation used to compare
identical blanks. These are changes to a new model's drilling layout, not
instructions to enlarge or redrill existing physical holes.

## Geometry result and remaining issue

The [trial](trial.json) moves 24 bolt axes, their complete occupied hardware
stacks, and the corresponding receiver bores. Finished receiver hosts are
rebuilt from raw timber plus all retained source cuts and current candidate
bores. All moved shafts have positive intersection with each intended raw
receiver and zero overlap with the newly bored finished receivers. Their
occupied shaft volumes inside each raw receiver also match the current
layout, so this screen found no loss of modeled wood grip. The
[finished-solid grouping](seven-design-grouping.json) confirms seven designs
for 24 placed blocks, allowing rotations but not mirror substitutions.

The full changed-hardware screen finds two timber intersections: the tails of
the bottom center rail bolts reach the enlarged central principal/header
blocks. These clashes already exist in the current model (about 19.10 mm³
per side); the common-pattern trial increases them to about 22.47 mm³. They
are not evidence that the current ten-design layout is clear.

A separate sensitivity shortens only those two occupied bolt shafts by 3 mm,
keeping their heads, washers and nuts at the same stations. Both shortened
shafts clear all modeled timber. The 149.4 mm trial shaft envelope is not a
purchased bolt-length selection or an instruction to cut a bolt. Actual
nominal length, nut engagement and delivered partial-thread shank still need
their appropriate later checks. No other changed-hardware hit was found
against the checked timber, other candidate hardware, existing frame bolts,
panel screws, T-nuts, LEDs, wires or provisional hold-bolt envelopes.

The block-body screen preserves the existing G2 LED and G12 provisional
hold-bolt overlaps at the affected blocks, with unchanged intersection
volumes. The trial does not resolve those existing design details.

## Recommendation and boundary

Use the shared pattern as the candidate for those fifteen blocks, with the
bottom-center bolt-tail detail resolved alongside it. If that detail is to be
handled separately, standardizing only the top-center pair and upper-left
inner block reduces ten designs to eight while retaining the bottom pattern.

Keep the shortened G7 block, kicker-post blocks, exterior spines, interior
sandwich blocks, and the two handed central header blocks distinct for now.
They have different bodies or drilling arrangements; they are not the same
near-identical-blank opportunity. Do not add unused holes merely to make a
part appear interchangeable.

This checks nominal geometry only. Tool access, edge/end spacing resistance,
wood grain requirements and complete joint behavior are not accepted. Joint
evaluations remain paused pending the owner's model review. The scripts saved
here consume the parent's already-built live CAD objects; they preserve the
comparison procedure, not a standalone baseline reconstruction command.
