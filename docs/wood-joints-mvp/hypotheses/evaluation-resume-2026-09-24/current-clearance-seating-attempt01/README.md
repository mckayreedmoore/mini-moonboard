# Current ordinary-patch clearance seating witness

This source-bound geometry witness reads the frozen 3-wood/4-bolt ordinary-patch inventory, contact classification, and material map. It records the cleat longitudinal grain direction, member grain axes, bolt axes, each receiver radial gap, and all three classified wood-face normals.

For each two-member bolted interface, both receivers have a 0.575 mm radial gap around the nominal shaft. A freely translating pin therefore permits a 1.15 mm relative bore-center separation disk. The rail-to-principal route through the cleat has two such interfaces in series along cleat grain N, giving a 2.30 mm translation-only free-travel scenario. The direct rail-to-principal coplanar face has normal +/-global X, tangent to N; normal-only face contact does not resist pure N translation.

This is conditional geometry/seating travel, not stiffness, response, capacity, or a full-assembly free-play bound. Member rotations are omitted; they are neither pinned nor accepted. Friction, preload, washer/nut lateral restraint, and other contact laws are unassigned. Only the three source-classified wood-face interfaces are checked; no other edge-contact or interference response is inferred. No CAD, mesh, or native solve was run. Inputs and producer/test hashes are listed in the witness, execution record, and `sha256.json`.
