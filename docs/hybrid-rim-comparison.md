# Hybrid rims against the plywood baseline

**Preliminary analytical section comparison—not new whole-frame FEA.**
The hybrid layouts have no backing or completed joints. Running them as complete
frames would require inventing load paths; the reference skins are not attached.
This screen isolates the side-rim depth change using the earlier model's assumed
E = 7000 MPa. It does not establish either candidate's adequacy.

## Results at equal assumed material modulus

All three side rims are 38.1 mm thick. Plywood lamination is assumed perfect.
For a member running uphill along the board, normal bending is bending toward
or away from its climbing face; lateral bending is across the board width.

| Quantity, relative to plywood side rim | Plywood | 2×10 | 2×12 |
| --- | ---: | ---: | ---: |
| Full section depth | 322.8 mm | 234.95 mm | 285.75 mm |
| Normal bending rigidity EI | 100% | 38.6% | 69.4% |
| Lateral bending rigidity EI | 100% | 72.8% | 88.5% |
| Gross volume at the same length | 100% | 72.8% | 88.5% |
| Extreme-fibre stress at the same normal bending moment | 1.00× | 1.89× | 1.28× |
| E needed to match baseline normal EI | 7000 MPa | 18,154 MPa | 10,091 MPa |

The 2×12 has about **1.80 times the normal bending rigidity of the 2×10** at
equal modulus. That gives it more stiffness to work with, not a strength rating.
Volume reductions apply only to equal-length side rims, not the complete frame;
mass also requires each material's density. Top caps and legs are not compared
by this table because their geometry and load paths differ between designs.

The material choice matters. At an **illustrative, unselected** lumber modulus
of 10,500 MPa, the 2×10 reaches 57.8% and the 2×12 104.1% of the baseline
normal EI. This is not evidence that purchased lumber has that modulus. The
generated record includes E = 3500, 7000, 10,500 and 14,000 MPa probes; these
are sensitivity assumptions, not certified properties or upper/lower bounds.
Wood properties vary with grain, growth features and conditions; see the
[USDA Wood Handbook, mechanical properties](https://research.fs.usda.gov/treesearch/62244).
The original plywood's isotropic E was itself an assumption, not a measured rating.

## What this says about the earlier numbers

The [updated plywood-frame study](updated-board-fea.md) reported **0.368 mm**
maximum displacement among five loaded nodes under 1.2 kN downward loading at
the 40 mm mesh. That was a 41-part, perfectly bonded, fixed-floor model without
holes or gravity. **Do not divide that displacement by the section ratios**:
the whole frame's response depends on its panels, backing, joints, leg geometry
and supports, not just side-rim EI. There is no hybrid counterpart to that
displacement result yet.

The [4.494 mm C10 connection result](panel-connection-comparison.md) is a
different local panel model with assumed attachment springs and rigid backing.
Changing rim width alone is not an input to that model, so rerunning it unchanged
would give no useful lumber comparison. Joint compliance and the new backing
load path must first be represented.

## Method and reproducibility

With thickness b and full rim depth h, use gross homogeneous rectangular sections:

```text
A = b h
I_normal = b h³ / 12       I_lateral = h b³ / 12
Z_normal = b h² / 6       Z_lateral = h b² / 6
rigidity = E I            bending stress = M / Z
```

These elementary cross-section calculations exclude holes, local bearing,
splitting, buckling, torsion, glue failure, shear deformation and connection slip.
They are not a plywood laminate or orthotropic timber strength analysis. No load,
support arrangement or deflection is invented for the incomplete hybrid models.
The comparison uses CAD constants for depth and thickness and records the hash
of the prior bulk-results file supplying the baseline modulus.

Run `uv run python -m fea.compare_rim_sections`; numerical evidence is
[`hybrid_rim_sections.json`](../fea/results/hybrid_rim_sections.json).
Run `uv run pytest tests/test_rim_sections.py` for formula, axis scaling,
input-validation, CAD-dimension and generated-record checks.

## What is still needed for the requested full comparison

Complete backing, panel attachments, kicker transition and detachable corner/
transverse joints in both variants. Then rerun the same six global load vectors
and row-12 targets, with matching mesh-refinement and support assumptions, to
isolate design effects. Record actual material choices and sensitivity cases.
Evaluate unanchored lift/slip separately; fixed-floor stiffness is not stability.
Finally evaluate the new joints with forces from the complete models. Neither
candidate should replace the default or be built based on this section screen.
