# Current washer bending and stiffness method attempt 01

**Reviewed:** 2026-09-28. **Candidate:** `led-clearance-2x6-runner-seated-blocks-v1`.
**Scope:** the `washer_bending` method question only. This packet is a source
and method review. It does not select hardware, calculate a candidate washer
response or capacity, change geometry, or change a criteria disposition.

## Finding

The method gap remains open. The current method map says the criterion is
pending and that no washer-bending producer or accepted capacity exists. The
coverage record likewise says no product is selected across all washer roles,
and no plate-response method or stiffness result is accepted. The current
schedule represents 92 candidate axes plus 12 retained frame axes, with 208
separate washer roles in total; the washer part identity remains unresolved.

Earlier reviews provide conditional facts for 20 candidate axes only: 16 side
axes and four outer-post axes. They discuss K.L. Jack 25NWUS Type A Wide plain,
low-carbon-steel washers as dimensional/material candidates. A separate
25NWUS8Z hardened washer description is also recorded, including ASTM F436
and a 38–45 HRC hardness range. Neither option was selected or received, and
neither cited product description provides a washer bending/load-deflection
rating or a numeric yield minimum. The existing property-basis note expressly
does not convert hardness to yield strength. These candidate-specific facts
do not bind the other washer roles.

## Evidence classes

### Direct product rating

No direct bending or stiffness rating was found in the product evidence used
for this review. The 25NWUS supplier entry is a dimensions/material listing;
the 25NWUS8Z entry adds a hardened-material description and hardness, not a
plate load-deflection curve or design resistance. ASTM F844-19(2024) covers
unhardened plain washers for general fastener use; ASTM F436/F436M-24 covers
hardened washers and specified chemical, mechanical, and dimensional
properties. Those product specifications are not, by themselves, a rating of
the washer in a particular head/washer/wood-seat assembly. ASME B18.21.1-2009
(R2016) supplies washer dimensional/physical-property requirements and
related tests; its public description does not identify an assembly-specific
plate-bending resistance method.

A manufacturer rating could be used only if it is for the exact selected
washer family and gives a relevant load-versus-deflection or resistance basis
with its material, geometry, contact, support, and test/application limits.
A washer hardness value or bolt proof load is not such a rating.

### Code methods

The reviewed AISC source set identifies the current ANSI/AISC 360-22 steel
building specification and the 16th-edition Steel Construction Manual's
member-flexure, connecting-element, and bearing-plate/base-plate material.
Those provisions are useful analogues for steel plate mechanics, but no
washer-specific method was found for a perforated circular washer loaded by a
bolt head or nut and supported through a nonuniform timber seat. A rectangular
base-plate or beam-strip formula would change both the plate shape and its
contact boundary conditions; it cannot be transferred without a separately
derived and validated idealization. The AWC/NDS wood-bearing reference beneath
a washer remains a timber check and does not determine washer metal bending
or stiffness.

This is a bounded source finding, not a claim that no code or manufacturer has
ever published an applicable method. None of the reviewed standards or
product sources supplies an accepted candidate method for this assembly.

### General plate-mechanics method

A defensible explicit mechanics route is a linear-elastic plate response
model whose geometry, load footprint, and support conditions match the actual
washer stack. For an isotropic thin plate, the classical flexural rigidity is
`D = E t^3 / [12 (1 - nu^2)]`; solving `D ∇^4 w = q(x,y)` with declared
boundary/contact conditions gives plate deflection and bending moments.
Those outputs can provide response/stiffness only for the stated elastic
model. A first-yield comparison additionally needs a sourced lower-bound
yield property and a stated stress interaction. Contact indentation, local
transverse shear, large deflection/plastic redistribution, and timber-seat
crushing need separately applicable treatment if they govern.

The primary annular-plate paper by Strozzi, Dragoni, and Ciavatti (1995)
derives a thin-plate flexural solution for an annular plate with a simply
supported inner boundary, free outer perimeter, and a concentrated transverse
load at an arbitrary point; it reports an experimental comparison for one
plate geometry. This is a useful annular-geometry benchmark, not the WJ24
washer boundary condition: the actual bolt-head/nut footprint is finite and
the timber seat is a distributed, potentially partial and compliant support.
Heap's Argonne report ANL-6905 (1964) is an additional primary benchmark for
thin circular plates under concentric ring loading and several specified edge
conditions. A small solver or analytic implementation could be checked
against a matching published case before any assembly model is attempted.

The method must not replace the real contact problem with an assumed uniform
annular pressure merely because a washer is round. For a final candidate
model, use the actual head/nut bearing footprint and actual timber support
polygon with cuts, holes, gaps, surface flatness, and timber compression
represented. A non-axisymmetric footprint or seat requires a two-dimensional
plate/solid model or a justified conservative reduction. Verify whether the
thin-plate and small-deflection assumptions apply to the selected thickness
and free span; if they do not, use a shear-deformable plate or three-dimensional
continuum/contact model.

## Exact inputs required before a candidate check

The following values must be bound to each washer role. These are input
requirements, not assignments or assumed values:

| Input group | Required evidence |
| --- | --- |
| Washer material | Exact product and standard; grade/type; heat treatment and material condition; traceable product or lot record; elastic modulus `E` and Poisson ratio `nu` for response; a sourced minimum yield or full stress-strain basis for any strength/capacity comparison. Do not convert hardness to yield without an independently accepted correlation and scope. |
| Washer geometry | Delivered or source-controlled minimum thickness and tolerance; inside/outside dimensions and profile; flatness/parallelism; burr/edge condition; coating or finish where it changes contact. Catalog nominal OD alone is insufficient. |
| Fastener contact | Actual bolt-head or nut bearing-face geometry, size, underside radius/chamfer, orientation, and the contact pressure/load distribution over the washer. Bind the head/nut part and axial force to each side. |
| Timber support | Finished support polygon after bores/cuts/reliefs, actual seat flatness and gaps, contact stiffness/compression basis, and the unsupported span between applied head/nut contact and active timber support. Do not assume a continuous full washer annulus is supported. |
| Actions | Fresh signed axial force at the actual bolt/washer stack, eccentricity and any co-located moment or shear that the chosen local model includes; state preload/load-history assumptions explicitly. No source-axis demand is substituted for a fresh candidate result. |
| Method applicability | Plate slenderness and small-deflection check; exact boundary/contact assumptions; stress recovery and yield interaction; validation against a matching analytic/experimental benchmark; separate treatment of any omitted contact, bearing, shear, plasticity, or cyclic effect. |

## Implementation decision

A generic, parameterized elastic plate-response harness can be implemented
before a washer SKU is selected or received. It can accept symbolic/test input
sets and be validated against a published annular/circular-plate known-answer
case. This would validate the mathematical producer only; it would produce
no WJ24 result.

The candidate producer cannot yet calculate an applicable response or
resistance. No washer is selected across the 208 represented roles, the actual
product material and dimensions are not bound, the support/contact fields are
not frozen, and fresh washer-side actions are not available. A strength
comparison also lacks a sourced washer yield minimum or a direct manufacturer
rating for the current conditional candidates. Therefore this packet
identifies a viable explicit mechanics family but does **not** close the
criterion's method/evidence gap. Keep `washer_bending` pending. Do not infer a
capacity from OD, thickness alone, hardness, a bolt proof load, or wood washer
bearing.

## Source trail

Primary standards and mechanics sources were checked on 2026-09-28:

- ASTM [F844-19(2024)](https://store.astm.org/standards/f844), plain
  unhardened steel washers for general use, and
  [F436/F436M-24](https://store.astm.org/f0436_f0436m-24.html), hardened
  steel washers. The repository's [ordinary nut/washer property basis](../../../current-ordinary-nut-washer-property-basis.md)
  records the public-property boundary for the 25NWUS and 25NWUS8Z conditional
  options.
- ASME [B18.21.1-2009 (R2016)](https://www.asme.org/codes-standards/find-codes-standards/b18-21-1-washers-helical-spring-lock-tooth-lock-plain-washers),
  the edition identified as remaining in effect by ASME on the check date.
- AISC [ANSI/AISC 360-22 current-standard record](https://www.aisc.org/aisc/publications/current-standards/aisc-360/),
  [revision/errata listing](https://www.aisc.org/aisc/publications/revisions-and-errata/),
  and [Steel Construction Manual, 16th edition](https://www.aisc.org/aisc/publications/steel-construction-manual/).
- A. Strozzi, E. Dragoni, and V. Ciavatti, “Simply supported annular plates
  transversely loaded by a concentrated force applied at an arbitrary point,”
  *Journal of Strain Analysis for Engineering Design*, 30(3), 211–215 (1995),
  [DOI 10.1243/03093247V303211](https://doi.org/10.1243/03093247V303211).
- J. C. Heap, “Bending of Circular Plates Under a Uniform Load on a
  Concentric Circle,” Argonne National Laboratory report ANL-6905 (April
  1964), [OSTI DOI 10.2172/4005214](https://doi.org/10.2172/4005214) and
  [UNT archival record](https://digital.library.unt.edu/ark:/67531/metadc868796/).

The exact local input hashes, version/identity pins, and online source notes
are in [`source-pins.json`](source-pins.json). Run
`python3 verify_packet.py` from any directory, or run
`sha256sum -c SHA256SUMS` from this packet directory. A source drift is
reported separately from packet-file checksum results.
