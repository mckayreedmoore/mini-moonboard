# Conditional left corner spine and block section forces

The source-bound calculation now supplies signed section resultants at four existing spine bore stations (BG001 and BG003) and two inner-block BG003 bore stations. It includes simultaneous neighboring bolt groups, timber contacts and each model's explicit source-discrete member loads. It consumes only the authenticated A12-rear, A1-rear and K12-rear responses; no rejected forward or lateral-case forces enter it.

[section-demands.json](section-demands.json) contains 42 body-state rows: three cases, seven increments and two members. Each of the six stations has just-below and just-above cuts, giving 252 one-sided results. The cut datum is the source member envelope axis at the stated global Z station. Each lower-segment material action is minus the sum of external forces and moments on that isolated segment; positive axial force is +global Z. The upper-segment convention and the coincident connector-force jump are separately retained. No force is spread across a bore or adjusted to improve equilibrium.

The following component magnitudes are maxima over the stated member's screened cuts at full load, **not simultaneous interaction checks**. Bending is the magnitude of Mx/My and torsion is |Mz| about the declared datum.

| Case | Member | Max axial magnitude (N) | Max XY shear (N) | Max bending (Nmm) | Max torsion (Nmm) |
| --- | --- | ---: | ---: | ---: | ---: |
| A12 rear | Spine | 317.47 | 237.48 | 12473.51 | 6529.45 |
| A12 rear | Inner block | 141.01 | 115.13 | 6256.07 | 3021.94 |
| A1 rear | Spine | 371.47 | 154.11 | 18088.38 | 1175.32 |
| A1 rear | Inner block | 109.75 | 145.65 | 6173.30 | 4044.54 |
| K12 rear | Spine | 65.48 | 178.66 | 4477.00 | 4011.41 |
| K12 rear | Inner block | 43.97 | 113.59 | 2304.49 | 4154.25 |

Parent [verification](parent-verification.json) independently reconstructed all 252 lower-segment actions directly from the native physical point forces and load-factor-scaled source nodal loads, with maximum force and moment difference zero. It does not reuse the corner exporter's force arithmetic. The producer also checks source hashes, increment identity, owner inventories, node/load coverage, source body wrenches, whole-body intervals, point-load jumps and both sides of each cut. Opposite reconstructed actions sum to minus the printed whole-body residual, rather than invented exact zero; the existing 0.1 N / 2 Nmm physical limits remain unchanged. Exported endpoint moment remnants are numerical zero (maximum 2.51e-13 Nmm in these inputs), not an extra physical couple to add.

This fills the signed-action gap only for the analytical source-discrete load distribution. Some source nodal loads have opposite signs as part of the source wrench-preserving distribution; they are not literal local physical gravity loads. A physical member self-weight distribution and section traction field remain unqualified. The old geometry-only net areas are included as context, without stress or resistance calculation. Adjusted member strengths, bore-section bending properties and concentration effects, applicable splitting/group/net-section rules, compatible BG003 bearing/contact and continuous-bolt resistance, washers and delivered shank/engagement remain missing. Three other load cases and physical stiffness bounds are unresolved. No complete-joint acceptance or fabrication claim follows.

Reproduce from the repository root:

```sh
python3 docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-corner-conditional-section-demands-attempt01/produce.py --verify
python3 docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-corner-conditional-section-demands-attempt01/parent_verify.py
```

Parent completed the Luna draft by reading the actual acceptance schemas, preserving original response gates, removing numerical couple roundoff, and retaining printed whole-body residuals explicitly. No geometry, native output, source load, spring law or full-frame tolerance was changed. The producer was not a frozen native input.

Subsequent context correction: this preserved JSON's inner-block BG003 cuts
carry the 11,766.458 mm² away-from-cross-bore area in their geometry-only
metadata. The applicable area at those center cuts is 11,099.708 mm² after
also removing the 666.75 mm² BG003 strip. The [net-section conversion and
independent check](../current-corner-net-section-normal-traction-attempt01/README.md)
explicitly correct all 84 affected context rows. The signed forces, both-side
reconstruction and native evidence remain unchanged; do not use the preserved
context field as a section capacity input.
