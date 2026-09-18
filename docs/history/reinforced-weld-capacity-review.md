# Frozen shoe weld: strength diagnostic and admissibility

The current fabricated shoe has one external 6 mm fillet. A direct-force weld-area check cannot qualify its six-component load path. Its particularly weak action is rotation about the weld's longitudinal global Y axis. A finite-throat elastic stress diagnostic is implemented in `fea/reinforced_weld_capacity.py`; it deliberately reports no qualification pass.

## Geometry and material condition

For the frozen 40-degree frame, the web's 105 mm normal width intersects the horizontal foot over `L = 105/cos(40°) = 137.067765 mm`. Its bottom endpoints are Y = −196.680818 and −59.613053 mm. The ideal throat is `a = 6/sqrt(2) = 4.242641 mm`; its area is 581.529278 mm². The right throat centroid is (1230.225, −128.146936, 236.025) mm, and the left centroid mirrors X. These are throat centroids, not triangular weld-solid centroids.

The calculation condition is an E70 filler with specified minimum tensile strength 70 ksi (482.633011 MPa), a sound full-length 6 mm fillet, and ASD resistance `0.60 FEXX / 2 = 144.789903 MPa`. No directional increase, penetration beyond the root, or contact/friction enhancement is taken. This gives a pure-direct-force diagnostic of 84.199568 kN. Those conditions require an actual weld specification and fabrication controls before they describe an installed weld.

## Six-component diagnostic

Supply force F and moment M of one cut free body about the throat centroid, including every bolt and contact action acting on that body. For side sign e = ±1, use short-throat axis `u = (e,0,1)/sqrt(2)`, longitudinal axis `v = (0,1,0)`, and normal `n = u cross v`. Resolve both vectors in this orthonormal right-handed basis.

For local coordinates x along u and y along v:

```
A = a L
Iu = a L^3 / 12
Iv = L a^3 / 12
J = Iu + Iv
normal = Fn/A + Mu*y/Iu - Mv*x/Iv
shear_u = Fu/A - Mn*y/J
shear_v = Fv/A + Mn*x/J
diagnostic = max(sqrt(normal^2 + shear_u^2 + shear_v^2)) / 144.789903
```

The maximum is evaluated at all four corners `(±a/2, ±L/2)`: the traction is affine and its norm is convex, so a rectangle corner attains a maximum. The traction field reproduces the six imposed section resultants. This is an elementary elastic section model, not a published AISC single-sided-root fracture model; in particular the polar-moment shear field is a resultant-equilibrating weld-group approximation, not a Saint-Venant rectangular-bar torsion solution.

`Iv = 872.293917 mm^4`, versus `Iu = 910460.280344 mm^4`. The pure longitudinal-axis elastic diagnostic is only **59.538085 N m**. Its pure-moment leg requirement is `w = sqrt(12 |My| / (144.789903 L))`, with N and mm units. This requirement is necessary to satisfy this particular elastic screen; increasing the leg does not itself establish root-rotation acceptability. Combined force and moment can require more than the pure-moment value. A zero-width line-weld model cannot represent this longitudinal moment at all.

## Primary-source interpretation and practical repair requirement

[AISC 360-16 Commentary J2](https://www.aisc.org/globalassets/aisc/publications/standards/a360-16-spec-and-commentary_june-2018.pdf), printed page 16.1-423, discourages one-sided fillets when the joint rotates around the weld toe. Its nominal fillet strength provisions support the direct-force value above; they do not supply the finite-rectangle longitudinal-bending model used in this diagnostic.

[AISC Modern Steel, January 2024, Steel Interchange](https://www.aisc.org/globalassets/modern-steel/archives/2024/january2024.pdf) explains that choosing a directional factor of one does not make every fillet configuration acceptable. It identifies outstanding-leg angle welds as having little resistance to longitudinal-axis flexural loading and says joint rotation still needs examination. This is AISC-hosted engineering guidance, not an additional mandatory Specification clause.

[AISC Modern Steel, January 2025, Steel Interchange, page 8](https://www.aisc.org/globalassets/modern-steel/archives/2025/january2025.pdf) cites Design Guide 21's instruction to prevent root rotation through stiffeners, diaphragms or the overall arrangement; relying on bolts requires a case-specific evaluation. The AISC-hosted [2023 Miller lecture abstract](https://learning.aisc.org/local/catalog/view/product.php?globalid=NASCC-2023-C1&lang=en_us) also identifies single-sided root bending as a nonuniform-stress connection needing special attention.

These references support a hard root-rotation detail gate independent of the numerical elastic screen. The frozen assembly has no second weld or steel stiffener that automatically closes that gate. Wood contact must not be silently treated as a permanent bilateral rotational restraint. Source retrieval encountered AISC maintenance/Cloudflare redirects; the 2024/2025 text above was available in the web index. A local file named `reinforced-aisc360-22.pdf` was a one-page challenge response when inspected, not usable 360-22 evidence.

If actual simultaneous demand fails the diagnostic or opens the root, a repair must either establish a compatible restraint against that rotation or provide a weld detail capable of transferring the longitudinal moment. A properly detailed complete-joint-penetration T-joint or a second fillet with sufficient separation are candidate mechanisms, each requiring fresh fabrication and load-path checks. The current inside timber seat leaves no room for simply adding the second fillet. A CJP replacement does not inherit a pass: as an initial scale calculation, the existing 9.525 mm A36 web's full-width elastic ASD first-yield moment is only 308.048475 N m using Fy = 36 ksi and Fy/1.67. This is a gross-section steel screen, not a CJP weld rating or a release instruction.
