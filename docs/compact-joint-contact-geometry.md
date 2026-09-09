# Compact joint: catalog-dimension contact hypotheses

This separate preparation retains the complete drilled compact rim and leg,
their four actual bolt axes and minimum-thickness MCX washer stacks. It does
not modify the frozen hardware viewer, member CAD or native evidence.

```sh
uv run python -m fea.compact_joint_contact_geometry --variant smooth --output fea/generated/compact-contact-smooth
uv run python -m fea.compact_joint_contact_geometry --variant root-reference --output fea/generated/compact-contact-root
uv run pytest -q tests/test_compact_joint_contact_geometry.py
```

The chosen dimensional case uses **maximum listed** head/nut flats (0.562 in),
head height (0.243 in) and nut height (0.337 in), not manufacturer nominal
dimensions. These are from the linked drawings for
[37C425HCS5Z](https://boltsandnuts.com/products/3-8-16x4-1-4-hex-cap-screws-grade-5-bolts-zinc-clear)
and [37CFHN5Z](https://boltsandnuts.com/products/3-8-16-grade-5-finished-hex-nuts-zinc-clear).
Regular hexagons have a fixed, recorded-by-geometry orientation; fillets,
chamfers and head bearing-face details are omitted.

Each end has two independent [MCX014423 washers](https://www.wroughtwasher.com/standard-washers/extra-thick-mil-carb-mcx/)
at their minimum listed thickness, 0.110 in (2.794 mm), retaining the existing
maximum-OD/minimum-ID case. The bolt origins shift to keep the actual wood
faces seated. Heads and shafts form integral bolts; washers and nuts remain
separate, for 26 bodies per joint.

Two explicit hypotheses replace the enlarged clearance-envelope shaft:

- `smooth`: nominal 9.525 mm cylinder throughout.
- `root-reference`: 9.525 mm to 74.6125 mm under the head, then an abrupt
  7.5692 mm (0.298 in) reference cylinder. This transition lies **inside the
  outer wood member**. The root reference is not a manufacturer minimum, and
  neither variant is a proven physical upper or lower resistance bound.

The nut bore matches the distal shaft diameter. Its coincident cylindrical
engagement patch is explicitly identified by an axial interval for a future
nut/shaft tie. No tie is currently applied. This is a planned elastic axial
retention idealization, **not resolved threads**, and must not tie the entire
shaft or any washer. It does not evaluate stripping, preload, loosening or
thread-bearing capacity. Helical geometry and actual runout remain unresolved.

Exclusive STEP export includes original-part hashes, source snapshots, stack
coordinates, dimensions and planned engagement. No mesh, material law, contact
law, boundary restraint, load, solver run or strength acceptance is supplied.

The left-side [smooth archive](../fea/results/compact-contact-smooth-v1.tar.gz)
and [root-reference archive](../fea/results/compact-contact-root-v1.tar.gz)
contain the STEP bodies, manifests and source snapshots. They are geometry
hypotheses, not completed joint analyses. Meshing must create an exact boundary
for the specified nut-engagement patch without merging unrelated contact
bodies or bonding the washer stack.

Verification: seven geometry/export tests passed (26.55 s), covering the
smooth and root-reference hypotheses, left/right root geometry, whole-member
and bore preservation, washer seating, hex/shaft/nut dimensions, exclusive
exports and source/STEP hashes. The interface list has 25 unique body pairs;
the wood interface is included only once. Ruff passed. No native solve ran.
