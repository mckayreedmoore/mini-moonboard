# Free-impact C3D10 method fixture design

Date: 2026-09-27. This packet prepares a bounded method fixture only. The
baseline and trace cases use the same input deck, in that order. No native job
or build is performed by this preparation.

## Model and known answer

The deck preserves the 54 physical node coordinates, twelve C3D10 tetrahedra,
and the two surface-to-surface contact faces from the reviewed point-trace
coupon. Upper nodes are `27` and lower nodes are
`27`; upper slave faces are elements 1–2 S1 and lower master
faces are elements 11–12 S3. Their planar interface area is 4 mm². The old
disconnected C3D4 witness is removed; node 8001 is instead a free U3
controller at `(1,1,1)` mm.

The lower block is fixed. Upper U1/U2 are fixed, and each of its 27 U3 DOFs is
related by its own homogeneous equation to the free controller U3. Initial
velocity is `−0.1 mm/s` for every upper physical U3 and the controller U3. No
load, motion amplitude, or damping is applied. With density `0.125 tonne/mm³`,
each 8 mm³ body has mass 1 tonne; the expected moving projected mass is the
upper 1 tonne and total element mass is 2 tonnes. This is specifically a
translation test, not the nut's eccentric pivot MPC.

The pressure-overclosure slope is `100000 N/mm³`, giving ideal scalar contact
stiffness `400000 N/mm` over the 4 mm² face. The discrete alpha-zero Newmark
oracle is copied from the pinned 70-state
[`parent-reference.json`](../implicit-contact-free-impact-design-attempt01/parent-reference.json)
(SHA-256 `fc63b21a5c9947f04dd1326339ba0201a2c251a465f41350fd35c46874198d61`). Initial energy is 0.005 N·mm. Maximum compression
is at increment 25; the endpoint unilateral switch opens at increment 50,
where the predicted energy increase is 4.28163131e−6 N·mm (0.0856326%). The
continuous event time is comparison only; the fixed-step recurrence is the
oracle.

The input hash is `2b253f63f9e8cee1bcb471ba3fb6b8150e72df781432bcfe6a1019e66d44caea`. Output requests are 55-node U/V DAT, 54-node
physical U/V FRD, upper and lower `ELSE,ELKE,EMAS,EVOL` totals, contact-energy
`CELS` totals, and pair-specific `CFN`. The trace case additionally records
the existing coupon-only `CCXPT_MAP` and corrected `CCXPT_TRIAL` lines. Require
70 accepted increment identities and match actual STA/CVG and FRD state times.
There is no fixed contact-point-count gate. The positive-gap MAP removal
condition and active compressed trial fields are interpreted using the pinned
trace field definitions. Old-set positive-gap TRIAL rows are diagnostic; later
regeneration removes positive-gap points, and accepted open states must have
zero active contact.

## Limits

This is a contact/inertia/output method fixture only. It does not establish
general C3D10 free-MPC inertia, the current physical-pivot map, a joint response,
wood bearing, friction, a capacity, or solver convergence in the full model.
The mass projection, initial velocity through the MPC, impact-energy branch,
CFN sign, and contact energy remain to be checked from the native records.
The parent runner owns freezing and serialized execution; the reviewer owns
the verifier and acceptance thresholds. The proposed output budget is 16 MiB
per case. Preparation status remains non-acceptance.
