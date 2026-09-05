# Hybrid connection development plan

Research checked 2026-09-05 against the complete 2×12 candidate. This is a
prioritized design plan, **not a rated hardware schedule or construction approval**.
The [current full candidate](hybrid-full-candidates.md) retains 20 custom angle
envelopes, 88 bolts and 132 screws. No component has been replaced by this review.

## Recommended direction

Keep the leg and rear-crossmember interfaces through-bolted for relocation.
Redesign permanent backing joints around side-grain attachments and direct
bearing where practical. Do not make the current long end-grain screws the
default purchase list. Resolve the footprint/load envelope before final joint
sizing: altered leg placement changes connection demand as well as stability.

The ordinary wood-screw end-grain issue is substantive, not just a missing
safety factor. AWC's corrected NDS commentary assigns no withdrawal design value
to ordinary wood screws installed in end grain because of variability and
splitting. This does not prohibit every proprietary structural screw:
Simpson identifies product-specific end-grain provisions for SDS/SDWS and certain
other tested screw families. Such an exception needs its own applicable report,
species, geometry and installation conditions; it cannot be transferred to the
current generic 4.826 mm screws. [AWC January 2024 corrections](https://web-media.awc.org/wp-content/uploads/2021/12/17210141/AWC-2015NDS-Updates-Errata_20240109.pdf),
[Simpson manufacturer technical Q&A](https://seblog.strongtie.com/2024/09/deep-dive-into-mass-timber-qa-from-our-virtual-summit-session/).

## Prioritized interfaces

| Priority / interface | Current unresolved behavior | Next candidate detail |
| --- | --- | --- |
| 1: four leg bolts per side | Plywood/lumber directional bearing, splitting, group action, hole slip, washer embedment, eccentric leg reaction; laminated-ply properties are not solid-lumber properties | Keep through-bolts provisionally; establish actual grade, thread location, washer/bearing-plate area, grain and plywood layup. Compare a bearing seat or distributed side plate if the calculated group demand warrants it. Do not assume four bolts share equally. |
| 1: normal rib to front batten | One front screw per rib enters its end; bonded bulk FEA conceals separation and rotation | Prefer a side-grain clip/blocking or gusset connection inside the permanent backing module. Preserve front screw/LED clearances. Check whether a direct bearing shoulder can carry compression while connectors carry opening and shear. |
| 1: rear crossmember to rim and rib | Custom 100×100×6 and 80×80×6 mm sharp angles have no rated capacity; eccentric bolt groups can pry and rotate | Compare a catalogued bolted angle with an engineered fabricated-angle detail. Re-layout around the selected hole pattern and edge distances; do not re-drill a rated bracket to fit existing coordinates. Keep removable interfaces bolt-operated. |
| 2: mid/seam/perimeter batten ends | Several end-grain screws; 138.9/189.7 mm lengths are geometric assumptions | Side-grain clips or screwed plywood gussets within a permanent backing module; use a listed structural-screw route only if its end-grain provisions actually cover the joint. Check panel-edge and wire access before selecting detail. |
| 2: top cap/rim and kicker-cheek splice | Top angles provisional; mixed plywood/lumber splice and short grain near kicker transition | Apply the same catalogued-or-designed angle decision at top; check cheek/splice shear, splitting, bearing and fastener layout with the resulting floor reactions. |
| 2: face panels to backing | Flush heads, plywood pull-through, shank shear/withdrawal, repeated removal and actual screw head shape unresolved | Select a documented structural panel-to-wood fastener with compatible countersink/head dimensions, length and penetration. Retain screws from climbing face into backing. Ordinary panel screws are not a reusable captive connection. |
| 3: two-layer plywood leg/cheek laminations | Perfect composite action is assumed, but glue specification and process are unspecified | Record plywood structural grade/layup, adhesive manufacturer and approved application, surface preparation, pressure, cure and moisture limits. Do not treat two purchased sheets plus unspecified glue as certified engineered lumber. |

## Product families worth detailing, not approved substitutions

- **Permanent small backing clips:** Simpson A35 framing angles, with the exact
  catalogued nail or approved SD Connector screw schedule. The manufacturer has
  an A35 installation guide and a connector-specific screw approval table.
  Check the actual load direction and lumber faces; a connector screw is not
  interchangeable with a generic wood/deck screw. These are candidates for
  permanent modules, not a proposal to repeatedly remove wood screws during
  relocation. [A35 installation](https://www.strongtie.com/resources/product-installers-guide/a35-studs-to-plate-condition),
  [approved SD connector combinations](https://www.strongtie.com/products/fastening-systems/technical-notes/sd-connector-screw-approved-connectors).
- **Detachable angle interfaces:** investigate the Simpson HL heavy-angle
  family first; compare its complete installation/load table against the actual
  joint. The current catalog also lists ML and reinforcing-angle families for
  alternative permanent details. No specific model, allowable load, bolt diameter
  or fit has been selected here. The 2026 catalog is the selection source, not
  a retailer's generic bracket description. Thin clips and heavy bolted angles
  are different connection systems. [Manufacturer connector catalog](https://www.strongtie.com/resources/literature/wood-construction-connectors-catalog).
- **Permanent structural screws:** Simpson SDWS Timber or SDS Heavy Duty
  Connector families merit checking where their documented installation matches.
  Their heads and diameters differ from the current countersunk envelopes, so a
  product change requires new CAD holes, clearance tests and joint calculations.
  End-grain permission and stiffness must be established separately from nominal
  screw tensile strength. [Manufacturer screw guidance](https://seblog.strongtie.com/2024/09/deep-dive-into-mass-timber-qa-from-our-virtual-summit-session/).
- **Through-bolts:** source traceable hex bolts, matched nuts and appropriate
  washers/bearing plates from a structural-fastener supplier. ASTM A307 Grade A
  hex bolts are one candidate specification, not an adequacy decision. Specify
  diameter, length under head, actual thread extent, steel specification, finish,
  nut compatibility and locking/inspection method. The present 3/8 inch CAD
  diameter and grip stacks are starting geometry only; supplier manufacturing
  ranges do not establish stock availability at every modeled size.
  [Portland Bolt timber fasteners](https://www.portlandbolt.com/about/industries/timber/),
  [A307 configurations](https://www.a307bolts.com/configurations/).

No manufacturer is being asked to approve this structure by association. A rated
connector installed outside its documented material, orientation, fastening or
spacing conditions does not inherit its tabulated rating. Preserve links rather
than republishing manufacturer documents.

## Inputs required before a capacity conclusion

- Lumber species, grade stamp, moisture/service condition and grain axes;
  structural plywood grade/layup and adhesive specification.
- Governing load combinations and application locations, including asymmetric
  loading and horizontal components; consistent allowable-stress or factored
  resistance basis. Do not compare an unqualified dynamic multiplier directly
  with a catalog load that already includes a duration adjustment.
- Final foot geometry, floor contact/friction assumptions and weight/centre of
  gravity, including the disposition of omitted holds and hardware masses.
- Product drawings, evaluation reports, exact holes and edge/end distances,
  threaded engagement, head/washer seating, tool access and relocation sequence.
- Connection force–displacement data or explicitly labelled stiffness bounds.
  An allowable load alone is not a spring constant; a measured elastic modulus
  alone is not a timber splitting or withdrawal resistance.

## Simplest credible connection-aware CalculiX route

Reuse the existing Docker/Gmsh/CalculiX workflow. The repository already has
`fea/solve_connection.py` for unilateral panel-head springs and compression
backing, `fea/check_unilateral_springs.py` for its element-law checks, and
`fea/solve_joints.py` for actual-hole bearing-traction submodels. These are useful
building blocks, **not an existing full nonlinear hybrid-joint analysis**.
CalculiX supplies spring and contact capabilities; use the manual/examples
matching the pinned solver version before extending the input deck.
[Official solver documentation and examples](https://www.dhondt.de/).

1. Retain the perfectly bonded bulk run solely as a stiffness comparison.
   Make separate mesh bodies at selected joints: coincident shared nodes or
   automatic ties must not silently bypass connector compliance.
2. Start with one leg-to-rim connection and one rib/front-batten interface.
   Represent bearing contact as compression-only and fastener opening/shear
   compliance separately. Distribute attachment forces over physical bearing
   patches, preserving resultant force and moment; do not attach a point spring
   to one arbitrary mesh node and interpret its peak stress as capacity.
3. Obtain stiffness from applicable data, or run clearly labelled bounds. Check
   release of the old tie, rigid-body modes, opening/slip direction, load sharing,
   mesh/penalty sensitivity, final-step convergence and force/moment equilibrium.
   Vary bolt-hole clearance and head seating; do not credit bolt preload/friction
   without a controlled tightening and retained-clamp-force basis for timber.
4. Introduce the calibrated/bounded interfaces into the whole-frame model.
   Apply gravity before climbing load and allow unilateral floor contact.
   Model sliding only with an explicit friction assumption. Artificial supports
   used for numerical stabilization must have negligible reactions and must not
   conceal tipping. Loss of equilibrium is a result, not a reason to fix the feet.
5. Extract joint demand envelopes, then use hand/code/product checks for timber
   bearing, splitting, withdrawal, pull-through, net section, group effects,
   bolt shear/bending and angle bending/prying. Local elastic FEA is useful for
   load distribution; it does not automatically predict wood fracture or fatigue.

Deliverable for the next joint iteration: one selected detail per interface,
traceable product/material inputs, revised clearance/assembly checks, and a
demand-versus-resistance table with unresolved entries plainly marked. Do not
spend effort meshing every screw thread before those choices are settled.
