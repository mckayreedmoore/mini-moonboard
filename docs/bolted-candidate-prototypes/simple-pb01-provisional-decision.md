# PB-01 rail provisional decision (Astra RV-2)

**Decision: revise the quarter-inch bolted solid-wood corner block family for
development only.** Historical code and documents call this part a `cleat`.
Do not advance this rail detail to the connected V4 candidate, release drilling,
or infer a rated joint. This is a bounded decision about what to investigate
next, not a rejection of every possible corner-block geometry.

The later [six-inch length trial](simple-pb01-short-block-screen.md) and
[two tension-only hybrid cases](simple-pb01-short-tension-component-comparison.md)
address bulk and axial-spring interpretation without changing this whole-joint
decision. Both cases retain 23 old connector proxies. The largest reported
conditional one-bolt lateral ratio is 0.0801, but group, washer, bored block,
physical contact and complete joint utilization remain unresolved. Treat the
older numerical table below as historical bilateral-model evidence only.

Run `uv run --no-sync python -m scripts.simple_pb01_provisional_decision` from
the repository root for the full signed JSON. The script writes no files and
runs no native solve. It uses the existing
[local-action extractor](../../scripts/simple_pb01_hybrid_local_actions.py),
[bolt component](../../scripts/simple_pb01_hybrid_component_comparison.py),
[member](../../scripts/simple_pb01_quarter_member_screen.py),
[cleat](../../scripts/simple_pb01_cleat_gross_section_screen.py), and
[rail stack](../../scripts/simple_pb01_rail_receiving_envelope.py) helpers.
The extractor authenticates the fixed four-contact a12-left archive and its
report, source snapshots, final cycle, contact state, connector ownership,
and equilibrium. The archive still models **23 other ML24Z/SDS stations as
old proxies**. It is one diagnostic hybrid, not final V4 demand.

The following actions are simultaneous within that one case, in global XYZ.
Forces act **on the host**; moments use the extractor's common PB-01 datum.
The JSON retains each signed bolt force and axial/lateral decomposition,
all four contact locations and active states per face, and equal-opposite
force and moment resultants on the cleat.

These are the archived **bilateral axial-spring** diagnostic actions. Negative
axial components are model output, not physical compression carried by an
ordinary unpreloaded bolt. A tension-only bolt/face-contact model must be
solved anew before using these axial values as washer or bolt demands; they
cannot be corrected by clipping this table after the solve.

- Principal–cleat: host force (−18.272, −2.815, −14.055) N; host moment
  (+825.136, −739.433, +132.376) N·mm; 2/4 active contacts, 12.281 N
  compression. Bolt u1 axial −0.635 N, lateral 14.939 N; u2 axial −5.356 N,
  lateral 27.399 N.
- Rail–cleat: host force (+18.271, +2.815, −1.664) N; host moment
  (−188.966, +1081.259, −132.382) N·mm; 2/4 active contacts, 8.710 N
  compression. Bolt r1 axial +31.367 N, lateral 12.799 N; r2 axial −22.122 N,
  lateral 15.321 N.

These are two interfaces in series. The bolt axial signs are spring actions
on the hosts, not established washer or bolt-tension demands. Compression
samples are point forces, not measured contact areas or pressure capacities.

The root-only, one-bolt lateral-yield helper gives the following
modeled-direction ratios for this case. It assumes dry DF-L, a 45,000 psi
bolt bending-yield input, no face gap, and thread root through both wood
members. Neither root diameter is a verified delivered minimum. The
0.189-in value is a typical root; 0.180 in is a sensitivity.

| Bolt | 0.189-in ratio | 0.180-in ratio |
| --- | ---: | ---: |
| Principal u1 | 0.0327 | 0.0347 |
| Principal u2 | 0.0606 | 0.0643 |
| Rail r1 | 0.0259 | 0.0275 |
| Rail r2 | 0.0317 | 0.0336 |

The ideal full wood-annulus reference is 216.68 lbf. Only r1 has positive
modeled host axial; its conditional axial/reference ratio is 0.0325. The
other three have no positive-axial ratio. Washer metal, seating, preload,
bolt steel/nut axial resistance, load sharing, and the oblique two-bolt row
group method are missing. None of these component ratios is joint utilization.

The six existing Appendix E member references range from 850.39 lbf for
the rail row toward the butt to 6,351.60 lbf for the cleat rail-hole net
tension section. The script reports all six reference values. It assigns
**no member utilization**: connector forces alone do not establish the
force at each critical section, its tensile or tear-out direction, or the
complete bored failure path. The cleat gross-screen reports a 0.007654 MPa
same-cut normal-tension corner maximum, 0.004174 MPa same-cut transverse
shear maximum, and 1,689.448 N·mm nonzero torsion. Bored net sections,
torsional stress, combined strength, verified wood properties and adjustment
factors are absent; cleat utilization remains null.

The fully threaded Everbilt 800676 rail lead passes only the *assumed*
independent stack intervals in RV-1. They are not product tolerances or
receiving acceptance. Actual complete threads, nut engagement, washer
dimensions, and bearing fit still need confirmation. The earlier nominal
partially threaded 5-in rail pattern cannot be treated as an accepted stack.

Revision work is therefore concrete: verify a purchasable rail bolt/washer
stack and root, establish member and bored-cleat critical-section actions and
strengths, resolve group/axial/contact load sharing on both faces, then test
the connected V4 topology across its six same-configuration cases. No absent
strength input is replaced with a made-up ratio. The old 23-proxy response
must not be promoted to that final demand set.
