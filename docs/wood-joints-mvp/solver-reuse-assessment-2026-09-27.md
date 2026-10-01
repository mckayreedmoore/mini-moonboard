# Solver and timber-model reuse assessment

Assessment date: September 27, 2026. Scope: the reviewed
`led-clearance-2x6-runner-seated-blocks-v1` wood-joint development candidate.
This is a software and input assessment, not a joint result or candidate
selection. No solver was installed or run, and no existing model was changed.

The best next investment is a bounded comparison using stock Code_Aster,
starting with the existing small analytical fixtures. It has documented
building blocks for this model. It is not a direct import, and a shared-node
contact issue needs checking first. OpenSees DowelType
and DOWEL are useful existing timber tools, but neither supplies the missing
current-joint response from geometry alone. This recommendation is an
engineering inference from the capabilities and inputs below; no comparative
performance has been measured.

## What the current model needs

The first representative patch is bottom-center-right: three timber bodies,
four bolt stacks and three timber interfaces. The frozen A09 model contains
19 bodies, 116,162 nodes, 57,643 C3D10 elements and 35 contact pairs. These
include eight shank-to-wood bore pairs, eight shank-to-washer bore pairs and
16 washer-seat pairs. Its four nut carriers use 24 coupling equations.
The [reproducible inventory](hypotheses/solver-reuse-assessment-2026-09-27/source-inventory.json)
records the source hashes and counts; its adjacent `inventory.py` reads the
existing inputs without modifying them.

The important response is the simultaneous load sharing between direct
timber contact and the bolted cleat path, including opening, bore clearance,
washer bearing, bolt bending and axial action. A single lateral connector
spring would omit parts of that system. The
[current response-method record](ordinary-joint-response-method.md) has no
adopted reduced law for those paths, and the
[resistance input manifest](hypotheses/evaluation-resume-2026-09-24/ordinary-patch-resistance-input-manifest-attempt01/README.md)
still has conditional hardware and resistance inputs. Switching software
does not resolve those inputs.

## Reusable options

| Option | What we can reuse | Fit for this task | Decision |
| --- | --- | --- | --- |
| Stock Code_Aster | Orthotropic elasticity, nonlinear contact, implicit dynamics, linear constraint equations and output machinery | Closest open-source replacement for the present detailed model; substantial input translation and verification | First comparison candidate |
| OpenSees DowelType | Implemented timber-joint force–displacement or moment–rotation hysteresis | Requires supplied response envelopes; not an automatic coupled 3D joint law | Keep for later frame reduction |
| DOWEL / DHYST | Single-fastener beam-on-foundation mechanics, layered embedment and clearance | Useful component comparison if applicable embedment data are available; cannot replace the complete block joint | Reference/component option |
| Existing resistance calculations | Conditional bolt, bearing and timber checks already in the repository | Answer capacity questions within their applicability; do not determine contact load sharing | Continue using alongside response analysis |

[OpenSees DowelType](https://opensees.github.io/OpenSeesDocumentation/user/manual/material/uniaxialMaterials/DowelType.html)
accepts exponential, Bezier or piecewise envelopes and has a bolted
moment–rotation example. Its initial stiffness, envelope, peak/descending
behavior and hysteresis parameters are inputs. Our inference is that copying
the example coefficients would substitute another joint's behavior. A useful
reduction needs supported directional envelopes and a component arrangement
that preserves the seat and bolt load paths; independent springs also need
evidence for their treatment of simultaneous actions.

[DOWEL's author documentation](https://alexschreyer.net/projects/dowel-software/)
describes a single fastener modeled with beam elements and nonlinear
foundation layers, including compressive-only response, hole tolerances,
axial action and a head-restraint spring. It needs fastener properties and
six-parameter layer embedment behavior from data or its database. The offered
installer is version 1.6.1017, listed as a 2005 release targeting Windows XP.
It is free of charge with separate license terms; open-source reuse and
runtime compatibility are unestablished here. Database applicability to this
DF-L material, bolt and grain directions is also unestablished. If applicable
parameters can be sourced, its component curves could support a reduced
assembly without our implementing a new bolt/embedment constitutive law.
Surrounding timber seats, group load sharing and actual washer/nut-stack
compliance still need supported assembly modeling.

These tools show that timber analysis is not limited to testing every proposed
assembly in a laboratory. They also show where test-derived behavior enters
the calculations. Applicable literature, database or mechanically derived
inputs may avoid new testing; new physical tests are not an automatic
requirement of this assessment. Reusing a solver or a published model does not
automatically supply applicable material data or every failure check.

## Code_Aster migration assessment

The [official download portal](https://open-simulation-center.org/downloads/code_aster/code_aster/17.4.0)
currently lists 17.4.0 as stable, with solver-only Linux/container options.
This assessment uses its v17 documentation as the prospective method basis;
no executable is pinned yet. A trial must record the actual binary/image
digest and matching documentation before running. The
[current documentation homepage](https://codeaster.gitlab.io/doc/docaster/manuals/man_u/other_pages/home/index.html)
is already v18, so following default documentation links indiscriminately
would mix versions. A full Salome-Meca GUI is optional for our scripted work;
the [product description](https://code-aster.org/en/product/main) distinguishes
the solver from the integrated modeling interface.

| Existing model obligation | Documented route and required translation |
| --- | --- |
| Directional timber elasticity | `DEFI_MATERIAU / ELAS_ORTH`, with assigned material axes; verify Poisson-ratio conventions and rotations against the current stiffness tensor |
| C3D10 volume meshes and named faces | Convert volume connectivity to the corresponding quadratic tetrahedra and contact faces to correctly oriented skin elements; audit connectivity, volumes, ownership and normals |
| Frictionless separation/contact | `DEFI_CONTACT` with nonlinear analysis; choose a compatible formulation and preserve gaps and unilateral behavior |
| Weighted port and nut equations | `AFFE_CHAR_MECA / LIAISON_DDL` can express linear equations; preserve the existing equation space and force/work mapping |
| Nut carriers | A separately verified rigid-carrier representation with the present zero-mass assumption; do not interpret the solid display envelope as a physical threaded nut |
| Free startup motion | `DYNA_NON_LINE` provides an implicit dynamic route; a free static mechanism remains a mechanism in the new solver |
| Reactions and contact history | Contact status/gap/resultant fields plus an independently checked extraction of port work and joint resultants |

The [orthotropic material documentation](https://code-aster.org/doc/v17/manuals/man_u/u4/u4.43.01/Caract_ristiques__lastiques_g_n_rales.html)
and [constraint documentation](https://code-aster.org/doc/v17/manuals/man_u/u4/u4.44.01/Chargements_de_type_Dirichlet_.html)
support these routes. `LIAISON_RBE3` also distributes resultants, but it is not
automatically the same weighted map we already have. `LIAISON_SOLIDE` has
small/large-motion distinctions. Matching the present infinitesimal nut-fit
equations and carrier behavior therefore needs a small rotation test, not
just a similar command name.

A concrete issue appears before any solve: the existing slave groups
`WJCP_N_001_S` and `WJCP_N_002_S` share seven nodes. The inventory checks the
producer's node sets, not independently reconstructed face connectivity.
The [v17 contact documentation](https://code-aster.org/doc/v17/manuals/man_u/u4/u4.44.11/Principes.html)
requires pairwise disjoint slave surfaces for the continuous formulation.
This flags a direct-import conflict to verify against the actual face
connectivity. Reversing pair 002's master/slave assignment in a hypothetical
node-set screen removes all slave-node overlaps across the 35 pairs. This
looks like a tractable translation issue, not a demonstrated solver blocker.
No deck was changed: connectivity, normals, gaps, pairing and mechanical
response under that reversal remain unverified. Silently dropping shared
nodes or replacing interfaces with ties would change the mechanics.

That contact documentation also cautions about local gap violations on
curved quadratic faces. It distinguishes nodal contact forces from pressure:
`CONT_NOEU` force components need resultant interpretation, while LAC uses
different element output. These are reasons to test the actual bore/edge
features and force extraction, not reasons to reject the software outright.

The [dynamic operator documentation](https://code-aster.org/doc/v17/manuals/man_u/u4/u4.53.01/Op_randes.html)
provides an energy balance and consistent-mass implicit dynamics. It also
documents restrictions on lumped mass and a different interpretation of
time-dependent imposed motion in explicit analysis. An explicit deck is
therefore not the first migration target. Implicit inertia and the current
massless constrained carriers still need verification.

## Bounded next experiment

Use a stock stable solver with no constitutive extension or contact-source
patch. The useful work would be an input/output adapter and method checks:

1. Verify units, orthotropic axes and a force/work-preserving linear port map
   on known elastic responses. Verify the actual nut-map translation and
   small-rotation inertia, including the zero-density carrier.
2. Verify opening, compression, reopening and free impact on small contact
   fixtures, including intermediate states. Test the shared-edge and curved
   quadratic-face features that occur in this patch. Establish a documented
   formulation/orientation without losing any physical interface.
3. Only after those checks, translate the representative three-timber,
   four-bolt patch. Preserve its clearances, frictionless assumption, numerical
   penalty interpretation, port work and nut-coupling limits. Compare
   equivalent physical cases; do not use an old gauge-force deck as the
   replacement for the later port-motion deck.
4. Judge progress by correct resultants, gaps, energy and sensitivity to
   timestep/contact enforcement/mesh, not convergence alone. The existing
   one-millimeter motion has an ideal clearance mechanism; a new solver is
   not expected to manufacture bore resistance before engagement.

A bounded DOWEL component comparison is also worthwhile if screening finds
applicable embedment parameters. It could provide independent bolt/clearance
curves before or alongside the Code_Aster trial. Do not make a full reduced
assembly depend on fitting unknown parameters merely to obtain a curve.

Stop this comparison if stock documented functionality cannot represent the
required contact topology or constraints, or if elementary mechanical answers
fail after input errors are resolved. That is a reason to reassess the method,
not to start another open-ended solver modification effort. Passing these
checks would establish a usable numerical route; candidate-specific strength,
stiffness, failure-mode coverage and six-case demand work would still remain.

The main migration cost is verifying contact and constraint equivalence,
not recreating the CAD or writing finite-element algorithms. There is no
measured runtime or calendar estimate. The selected baseline, reviewed
geometry, other agent's work and existing acceptance records remain unchanged.

Two Luna agents at maximum reasoning effort independently reviewed the solver
migration and timber-model claims. Their findings are incorporated, including
the pair-002 orientation screen and DOWEL's axial/head-restraint capabilities.
Validation reproduced the hashed input inventory and checked local report
links. These reviews and checks are not native mechanics results.

After this assessment, the owner authorized the bounded stock-solver trial.
Its separate [native trial results](hypotheses/code-aster-stock-trial-2026-09-27/RESULTS.md)
record the tested methods and remaining candidate-specific applicability work.
