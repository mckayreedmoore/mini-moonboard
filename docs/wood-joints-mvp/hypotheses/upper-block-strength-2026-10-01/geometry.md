# Upper block geometry and applicability inventory

This inventory pins the reviewed `led-clearance-2x6-runner-seated-blocks-v1`
geometry and the saved A12-rear, A1-rear, and K12-rear bolt actions. It covers
eight blocks and 32 physical bolt axes. The two source reports contain 672
sampled bolt-state rows and 1,344 block/host member-direction rows. They also
pin 15 unique member STEP solids by path and SHA-256.

The [replay script](geometry.py) verifies both source JSON hashes, checks
action-to-axis identity and signed direction projections, verifies each
referenced STEP hash, then rebuilds the ignored
`geometry.json`. It samples exact block sections only; it
does not assign loads to those sections.

## Outer top blocks

Each outer top block has two separate two-bolt groups: a rail pair into its
rail host and a side pair into its side host. Both pairs have 33.0 mm
center-to-center spacing. For the cleat, the rail pair's pitch is parallel to
the conditional grain axis and the side pair's pitch is perpendicular. Those
relationships reverse in the corresponding hosts. The pair records are
geometric groupings; they do not establish a group factor, independently
resisting capacities, or splitting resistance.

The largest sampled side-2 vectors are the first priority in the saved action
records. Equal-and-opposite member directions give each bolt the same
resultant magnitude, while conditional grain axes rotate the directional
components between block and host:

| Block and side-2 member | Maximum lateral resultant | Sampled angle to conditional grain | Minimum outer-box grain-end distance |
| --- | ---: | ---: | ---: |
| Left cleat, block | 1,074.8 N (A12-rear, factor 1.0) | 0.46° to 4.73° | 59.85 mm |
| Left cleat, host | 1,074.8 N (A12-rear, factor 1.0) | 85.27° to 89.54° | 66.00 mm |
| Right cleat, block | 1,264.7 N (K12-rear, factor 1.0) | 0.06° to 4.53° | 59.85 mm |
| Right cleat, host | 1,264.7 N (K12-rear, factor 1.0) | 85.47° to 89.94° | 66.00 mm |

The saved vectors have nonzero grain-parallel and cross-grain components in
all 21 states for each of these member directions. The angle ranges are
therefore a description of the sampled oblique vectors. The conditional 4D
edge and 7D parallel-tension end values elsewhere in the inventory remain
pure-direction geometry comparators; no comparator is applied to the
simultaneous oblique vector as a capacity rule.

The source outer-box comparison identifies several short conditional end
distances: 27.9 mm at the top-center principal host, 43.35 mm at an ordinary
cleat rail axis against a 44.45 mm 7D reference, and 26.95 / 59.95 mm at the
two G7 rail axes. These are directional outer-box distances only. The input
geometry explicitly excludes bores, seats, cuts, and other nearer boundaries
from that comparison. No cross-grain loaded-edge distance in the 64 direction
rows is shorter than the conditional 25.4 mm 4D value. These results do not
establish NDS applicability, adjustments, or a completed member check.

## Exact block sections

The replay imports each of the eight hash-verified block STEP solids and cuts
planes normal to its declared conditional grain axis. For each block it
samples each distinct bolt mid-bearing station and the midpoint between each
adjacent station. Four bolt axes resolve to three distinct stations: one
outer axis at each end and two axes at a shared center station. This produces
five samples per block, 40 in total.

The query sums areas of OCC's trimmed planar section faces and reports their
count and individual areas. Because it sections the pinned BReps, modeled
bores and cuts are present in these geometric areas. The common-size blocks
and shortened G7 block have these sampled patterns:

| Sample location | Exact section area | Connected section faces |
| --- | ---: | ---: |
| Either outer bolt station (one axis at station) | 7,236.46 mm² | 2 |
| Center bolt station (two axes at station) | 6,569.71 mm² | 3 |
| Either midpoint between adjacent bolt stations | 7,903.21 mm² | 1 |

Individual component face areas and exact global plane coordinates are in
the local-only `geometry.json`, by block and sample ID. The measured face
counts describe connected material regions in each sampled plane. The
midpoint sections are explicit samples, not evidence that no smaller section
occurs between samples. No critical section is extrapolated or selected.
The replay records CadQuery 2.8.0 and OpenCascade 7.9.3.1 with the section
results so a different geometry-kernel version is visible during comparison.

## Applicability boundary

The exact block STEP source and sampled section area are available for each
block. The member force and moment assigned to any cut remain open. This
inventory calculates no section stress, net-section resistance, splitting
capacity, interaction, or NDS adjustment. The host directional records retain
their hash-pinned STEP references, but host section cuts are outside this
bounded eight-block section query.

The two source reports remain conditional inputs. The inventory does not
establish complete joint resistance, a six-case envelope, physical inspection,
drilling, fabrication, or structural release.

Replay the inventory and run the focused checks from the repository root:

```sh
.venv/bin/python docs/wood-joints-mvp/hypotheses/upper-block-strength-2026-10-01/geometry.py --verify
.venv/bin/python docs/wood-joints-mvp/hypotheses/upper-block-strength-2026-10-01/test_geometry.py
```
