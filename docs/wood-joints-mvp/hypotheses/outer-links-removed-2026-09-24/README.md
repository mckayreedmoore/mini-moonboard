# Outer supports removed and corner-block count

The owner requested removal of both rear crosspieces and both underside
corner blocks after adding the outer sandwich connections. The current
viewer revision is `outer-rear-bridges-under-header-links-removed-v1`.
Four parts and twelve associated bolt stacks are removed. The header and
outer spines are rebuilt without obsolete holes; the outer post bolts, shared
sandwich side bolts, and new inner-block header bolts remain. All 66 panel
screw axes and twelve starting frame bolts are preserved.

The [revision report](revision.json) records positive restoration volume at
every removed hole in a retained receiver and identity of the six retained
sandwich bolt axes. There are now 24 candidate blocks, 90 candidate bolt axes,
450 candidate hardware solids, and 495 viewer overlays. The source-bound
scene/report hashes are in [verification.json](verification.json). The live
viewer is at `http://localhost:8765/wood-joints-wj24-viewer.html`.

## Ten distinct block designs, twenty-four installed blocks

The [block grouping](block-designs.json) compares the actual finished solids,
including bolt holes and reliefs. Identical parts count together after a
translation or rotation; a reflection alone does not make two parts identical.
Candidate matches from principal inertia axes are checked by solid intersection.

| Distinct design | Installed quantity |
| --- | ---: |
| Common middle/outer-top block | 8 |
| Bottom rail blocks | 4 |
| Center kicker-post blocks | 2 |
| Top center blocks | 2 |
| Exterior sandwich spines | 2 |
| Interior sandwich blocks | 2 |
| Left central principal/header block | 1 |
| Right central principal/header block | 1 |
| Upper middle inner-left block | 1 |
| Shortened upper middle inner-right block near G7 | 1 |
| **Total: 10 designs** | **24** |

The left and right central header blocks remain distinct handed drilling
patterns. The detailed grouping records every part ID and the accepted rigid
transform for each duplicate. This is a geometric count, not approval of grain
orientation, manufacture or joint capacity.

The owner also requested a [hypothetical midpoint screen](../midpoint-clearance-2026-09-24/README.md).
Joint evaluations remain paused pending explicit owner sign-off. The existing
wire-routing, G2 light, G6 provisional hold-bolt and panel-edge support details
remain open; none is closed by removing these four supports.
