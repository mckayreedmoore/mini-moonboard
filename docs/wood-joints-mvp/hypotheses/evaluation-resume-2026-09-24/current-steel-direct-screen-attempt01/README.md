# T06 `steel_direct` source and method screen — attempt01

**Screened 2026-09-28. Finding: method gap remains; no criterion result.**
This is a bounded source review for the current through-bolted solid-wood
development candidate. It changes no criteria disposition, method map,
hardware/material selection, geometry, native/solver state, or release flag.

## Finding

I could not authenticate one applicable design procedure for the current
candidate's simultaneous bolt tension, transverse shear, and bending. The
official ANSI/AWC NDS-2024 Chapter 11 source, §11.2.3, directs metal fasteners
and other metal parts to applicable metal design procedures for tension,
shear, metal-on-metal bearing, bending, and buckling. It also says not to apply
wood adjustment factors where metal strength controls. That clause does not
select a specific procedure for these through-bolts or provide a fastener
section interaction equation.

NDS-2024 §12.3.6.2 and ASTM F1575/F1575M-24 identify a test basis for the
dowel bending yield property `Fyb` used to derive **lateral wood-connection**
values. ASTM F606/F606M-26a is a fastener test-method standard; its scope says
the product standard supplies property requirements and applicable tests.
These sources supply ways to obtain material-test inputs. They do not, by
themselves, establish a direct bolt tension/shear/bending design resistance or
a combined axial/lateral/moment acceptance rule. The NDS lateral-yield and
TR12 path remains a distinct wood-connection method, not proof of an
independent bolt steel check under simultaneous axial action.

The AISC material screen does not close the gap. AISC identifies 360 as its
structural-steel building/structure specification and RCSC as covering bolted
structural-steel joints. The current official pages were discoverable, but
the full current 360 text was not accessible in this screen. No AISC equation
was adopted or transferred to this wood joint. A primary AISC research paper
on combined tension and shear discusses von Mises and an empirical interaction
proposal, but it is neither a current normative rule nor a bolt-in-timber
method, and it does not include bolt bending.

## Producer decision

**No criterion-resolving `steel_direct` producer is ready to implement from
the available method evidence.** A generic input contract could be written,
but it would have to return `pending` until the design procedure, product
property basis, section map, and current actions were supplied. The existing
[`wood_joint_bolt_resistance.py`](../../../../../mini_moonboard/wood_joint_bolt_resistance.py)
already reports unadjusted material first-yield references for direct tension
and shear, and an optional nominal same-section von Mises axial/shear value.
It labels bending unevaluated and excludes design factors, fracture,
stress-concentration, load-sharing, and joint effects. Those numbers are
material references, not design resistances or connection acceptance.

The current product screen has no fit-qualified SKU. The pinned geometry has
92 candidate bolt axes and 12 retained frame-bolt arrangements, but the
current full-frame manifest has no solver-ready model or current bolt demands.
Its six records are applied load/wrench inputs only. A later producer needs a
chosen applicable metal procedure and product/property basis, actual thread
and shank sections at each tension/shear/bending section, actual shear planes,
fresh signed simultaneous bolt forces and moments, and an independently
checkable benchmark. No capacity is inferred here.

## Small arithmetic known-answer

[`known-answer.json`](known-answer.json) checks only the existing helper's
synthetic material-reference arithmetic with an explicitly co-located area.
It is not a bolt scenario, design resistance, demand, or criterion result.
The shear stress is the helper's nominal average `V/A`; this does not validate
the stress distribution or interaction applicability for a real bolt.

## Frozen context and scope

The source pins are in [`source-pins.json`](source-pins.json). The geometry
revision is `led-clearance-2x6-runner-seated-blocks-v1`, reviewed at repository
commit `b1e8707d`. The pinned development solver profile is CalculiX 2.23, but
the manifest says no native solve was executed, no current frame demands are
available, and solver material/body mapping is incomplete. This screen used
no solver and made no solver-state change. Preserve this method gap until a
source-supported applicable design route is resolved.
