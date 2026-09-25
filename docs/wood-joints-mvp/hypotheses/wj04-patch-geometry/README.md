# Representative ordinary-joint geometry export

Status: verified geometry export only, 2026-09-24. The parent exported five
independent finished wood solids from retained WJ16 geometry in 1.26 seconds:
the two right service rails, right center principal, and two G7 cleats.
The [bundle inventory](../../../../fea/results/diagnostics/wj04-full-stock-patch-geometry-v1/inventory.json)
binds eight physical bolts, forty separate hardware shape roles, four wood
interfaces, declared grain frames, and source cut/receiver metadata. Hardware
is described separately; it is not fused into the timber or exported as STEP.

All five STEP readbacks match source solid count, volume, centroid, bounds,
and shape. Source-only and STEP-only Boolean volumes are zero for every body.
The allowed symmetric-difference residual is `0.001 mm³ + 1e-9 × max(volume)`;
the inventory records that threshold and each measured residual. Face ordinal
matching is not used. A focused regression confirms that compensating hole
changes can pass volume/centroid/bounds checks yet fail the shape check.

The producer rejects changed frozen input hashes, mismatched live composition
or mechanics reports, wrong body/bolt/receiver identities, and existing output
destinations. Eight focused tests and Ruff pass. The [execution record](execution.json)
and [source manifest](sha256.json) bind the parent run and snapshots; the
[bundle manifest](../../../../fea/results/diagnostics/wj04-full-stock-patch-geometry-v1/sha256.json)
binds the five STEP files and inventory.

A subsequent [parent face-overlap probe](finite-face-overlap.json) intersects
the actual opposed planar faces, without translating or projecting them.
Each of the four interfaces has one matching face on each member and one
finite common face. The two lower areas are 10,552.972707 mm² each; the two
upper areas are 7,637.052707 mm² each. Principal face distances are zero;
rail face distances are about 2.3054e-7 mm, within the probe's 1e-6 mm plane
selection tolerance. These are nominal CAD intersections under kernel
tolerance, not physical flatness, seating, or active pressure measurements.
The archived probe is a bounded investigation; solver surface ownership and
contact activation still need implementation and validation.

This is preparation for the [response method](../../ordinary-joint-response-method.md).
Mesh, material/contact laws, active pressure, response, and resistance remain
unresolved. Exported CAD is not inspected lumber. No native solve or release
follows from this result.
