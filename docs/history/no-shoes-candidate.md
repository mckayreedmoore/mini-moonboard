# Single-2×6 support-leg candidate without custom steel shoes

> Historical `no-shoes-development` baseline. Forward-looking analysis notes below describe that earlier stage, not the selected exterior revision. See the [current design basis](current-design-basis.md) and [completed exterior assessment and package](clear-space-study.md). Historical force results and machining do not transfer to the selected assembly.

This separate development candidate removes the custom steel base shoes from
the published four-bolt 2×6 support-leg design. It restores the preceding
rim-to-header detail: two Simpson ML24Z angles with twelve specified SDS screws,
and the original timber bearing ends. It is a fresh-stock design, not a repair
for rims already shortened or drilled for the shoes.

The support legs and outer rims remain single nominal 2×6 members. Other frame
stock retains the existing design sizes; this is not an all-2×6 frame. The eight
complete leg bolt stacks, accepted panel construction, 142 modeled T-nuts and
ten additional kicker-header screws remain. Hold bolts are not added.

## Kicker and pad height

The requested floor-to-main-face datum is **277 mm (10.91 inches)**:
150 mm of exposed kicker plus a 127 mm (5-inch) pad allowance. The preceding
model used 225 mm, so this candidate raises the main assembly by **52 mm**,
not by a further 127 mm. The pad is a clearance allowance, not a structural
support or a modeled foam-compression prediction.

Supporting posts, rear legs and kicker plywood must reach the original floor
after the upper assembly is raised. The rear legs retain their grain direction
and section; extending them to the floor also changes the rear footprint.
Hold, LED and connection locations above the extension move with the assembly.
The floor remains the structural datum. The existing panel seam profile governs
the physical plywood edge at the transition to the sloping face.

## What removal changes

The custom shoes, their sixteen bolt stacks and associated bearing plates are
absent. Original rim bearing geometry and commercial angle connections replace
them. Shoe holes and the 9.525 mm shoe-clearance cuts are not retained in the
new timber. Panel attachment layout and LED access remain unchanged.

The [current equilibrium calculation](current-frame-equilibrium.md) uses this
candidate and the agreed assumption that the feet do not slide. Internal member
and connection forces still need to be calculated using published material properties. Removing the shoes
changes joint stiffness, load transfer and assembly weight. Neither the previous
2×6/2×8 force comparison nor the shoes' analytical results qualify this candidate.
The commercial angles' ability to carry the resulting frame actions remains to
be checked; restoring their geometry is not a strength approval.

No plywood or T-nut upgrade is proposed. Their accepted construction remains
the design basis. The next analysis should identify any specific deficiency
before adding material or changing those components.

## Files

- [Interactive viewer](https://mckayreedmoore.github.io/mini-moonboard/?model=no-shoes-development&view=rear)
- Candidate source: [no_shoes_frame.py](../mini_moonboard/no_shoes_frame.py)
- Viewer inventory: [parts.json](../site/hybrid/no-shoes-development/parts.json)
- Export provenance: [manifest.json](../site/hybrid/no-shoes-development/manifest.json)
- Complete CAD assembly: [assembly.step](../site/hybrid/no-shoes-development/assembly.step)

**This is a development candidate and has not been released for construction or climbing.**

Focused checks cover the restored hardware inventory, raised datum,
floor-contact extensions, retained leg sections, kicker-screw clearance against
the restored angles, and source/artifact provenance. The current exporter builds
all 703 viewer parts in assembled world coordinates directly from CAD, including
separate bolt components and electrical display envelopes. It no longer reads
historical meshes or their manifests. The browser check verifies standalone
mesh loading and floor-contact coordinates. A clean temporary rebuild check is
available with `uv run python -m mini_moonboard.no_shoes_exports --check` and
runs in CI. These checks establish the intended geometry, not structural capacity.
