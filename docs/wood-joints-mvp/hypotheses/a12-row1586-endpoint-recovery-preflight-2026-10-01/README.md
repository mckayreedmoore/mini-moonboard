# A12 raw-H row 1586 endpoint-recovery preflight

This packet prepares a parent-only, two-body recovery for the worst normalized
raw-H force interval at source row 1586 (`SPR1787`, element 3690). No existing
packet recovers raw-H physical endpoint vectors: the raw-H comparison saved
connector forces, rigid coordinates and scalar projected `q`, but no endpoints;
its force diagnostic leaves `dd - dd0` unevaluated. Attempt04 replay covers the
authenticated native A12 response, while attempt04 compliance contains `H`,
`D`, `e` and `W`, not this raw-H body's endpoint response.

The target owners are `left_service_inner_lower_cleat` and
`base_rail_service_lower_left`. The preflight pins the raw state, A12 rear
source gravity and climber maps, original stiffness and DOF map, physical
connector projection and ownership map, attempt04 reduction methods, emitted
deck, modeled solid mass centers, and the adjacent ghost-coordinate
diagnostic. It rebuilds `B` from the source projection contract and physical
index map, and independently reconstructs both source loads and wrenches. It
does not call the compliance producer's extraction or wrench helpers.

The direct reconstruction reproduces attempt04 physical `B` exactly (1,840
rows, 37,647 physical DOFs, 62,607 nonzeros). For each body, the independently
reconstructed six columns of `B*R` match the pinned `D` block exactly. This
identifies the unchanged raw-H body-equilibrium gate's reference as the node
arithmetic mean used by the rigid basis. The independently reconstructed A12
gravity/climber wrenches match saved full-load `W` within `1.84e-15` in scaled
generalized coordinates, and the raw body loads match the negative saved
`D.T*f-W` residual within `9.77e-15` scaled N. The target connector action
uses the source sign `-B.T*f`. Emitted MPCs and endpoint equations match the
deck within `4.89e-15` in rounded coefficients.

The packet distinguishes four points. The source body-wrench audit reports
moments about the global origin; the A12 nodal-map reconstruction matches its
force and moment within `7.2e-15 N` and `7.3e-12 N mm` for the base rail, and
`7.0e-18 N` and `1.2e-13 N mm` for the cleat. The raw-H `D.T*f-W` gate stays at
the node-mean rigid-basis reference with its original componentwise limits of
`0.1 N` and `2 N mm`. The geometric descriptor endpoint midpoint is separately
recorded. The fourth point is the pinned modeled-solid mass center; it is not
an as-built physical center. The descriptor midpoint and node mean happen to
agree to roundoff for these two bodies, while the rail modeled mass center is
`0.83054 mm` away and the cleat modeled mass center is `0.00845 mm` away.

Every reported wrench is transported using
`M(r) = M(c) - (r-c) × F`, including its residual force. Thus the original
component moment gate is not treated as invariant under translation. At the
modeled mass centers, the mathematical outer bounds transported from the
original component limits are `[2.00026, 2.08318, 2.08320] N mm` for the rail
and `[2.00006, 2.00088, 2.00087] N mm` for the cleat. These are not new gates.
The report provides transported A12-source, raw-H-load, residual and target-row
wrenches at the node mean, descriptor midpoint, modeled mass center and global
origin; the global-origin bounds show the larger possible force-offset term.

## Bounded recovery and known answer

A later parent-authorized run would be limited to the two pinned body blocks:
60 physical DOFs for the inner cleat and 276 for the rail. Each body would use
the unmodified original `K_b`, its exact six rigid columns, and the raw load
`F_g,b + F_c,b - B_b.T*f_full` in `[K_b R_b; R_b.T 0]`. It would combine the
recovered elastic field with that body's saved raw-H rigid slice as
`u_b = R_b*a_b + u_el,b`, then use the emitted MPCs at nodes 18266/18267,
18268/18269 and 21300 exactly. Node 21301 stays fixed. The result would use
the emitted endpoint coordinates and unchanged SPRINGA `dd - dd0` force law.
The 50-body stiffness map, source state, force law, source intervals, active
set and original `STOP` stay unchanged. No such factorization or recovery was
performed here.

The prescribed-answer oracle uses a four-node tetrahedron with six unit axial
springs. It checks prescribed elastic displacement against `K*u`, the rigid
gauge and free-body wrench, both interpolated endpoint vectors and scalar
extension back-projection, plus a signed endpoint force/couple transform. The
endpoint known-answer error is `1.78e-15 mm` and the wrench error is zero. It
assembles a 12 by 12 matrix but performs no factorization or solve.

The adjacent ghost-coordinate diagnostic is pinned and summarized in
`readiness.json`. Its common translation changes the force computed from the
final printed displacement tokens by `-3.3899844e-10 N`; both arithmetic values
remain inside the existing native RF interval, whose radius is
`7.0441603e-10 N`. The raw-H miss is `9.0355e-8 N`, 266.5 times larger. This
is a printed-U coordinate-arithmetic diagnostic, not a remedy: this packet
keeps original coordinates and MPCs and proposes no ghost or model shift.

## Original stop and reproduction

The raw-H status remains `STOP_PHYSICAL_OR_SOURCE_COMPARISON_GATE`, with all
27 force interval failures. Row 1586 remains outside its unchanged native DAT
force interval by `9.04e-8 N`, ratio `128.2644`. No correction, interval
change, force adoption, new case, contact-state selection or acceptance claim
is made. Printed DAT-U radii cover printed-token rounding; `q_raw` is a linear
projection; exact finite-span `dd-dd0` requires the recovered endpoint
vectors. These quantities remain separate.

Reproduce the source-only readiness and verify its frozen report with:

```sh
.venv/bin/python docs/wood-joints-mvp/hypotheses/a12-row1586-endpoint-recovery-preflight-2026-10-01/prepare_recovery.py --verify
```

The fresh readiness verification completed in about 1.3 seconds, read saved
inputs only, and performed zero native runs, factorizations or body-state
solves. The adjacent ghost-coordinate audit also passed its pinned source,
emitted-row, arithmetic and known-answer checks. Source
pins are in `source-pins.json`; its SHA-256 is
`25edf5239c59224e47cd5c6c4b5b2ce11a87b61890b6e2e0a38a1e05198699d2`. It
contains exact hashes for all 39 reviewed inputs, including:

- Raw-H response `2ada6877988c573fbfe89bb47b9945e774a8c373c250ad136e1124943ffa1a97`, raw-H producer `f39916598fb66bdbd2949c77b41adf64b6239fc1a14d7f96ee41b6e38ad095cc`, and force diagnostic `7542ce827f79bcdfe93c018e6b6f869f6435e8190a5ca0d5d492158961412658`.
- Original stiffness `7d22d2b013fcdc9fddfeab589b456615f0671db989a034e091bac855f3a93c01`, native DOF map `532f732e5b2ed88d96c544b73bcc33168a65942ff6c5155f30c6d4ade9173f1d`, and elastic quotient method `2275929b42dff5f03b4e822a8050631519d15e4e0a94ed6f604e065cab4dade6`.
- Attempt04 `B` `15470db045b2d78250cb96ec4a2a2c2d1d2f81a32c8408b08b96a8cb2ea1e220`, operators `88a2f2f384edb7be7daa0e20cc87c7b8672ed13e975f8e86afd56d8aeb385b79`, A12 source model `61f95ec9e670b2bd0e95d426cc14ff381283edfc4f9c87e47c2b344dd4fe50b8`, and A12 load maps `9cd59d7bbafd65c740d2b0200e3dd88a6a49e6dca0bead0a38bc7826e337548c`.
- Modeled mass-centers result `4c107b76d42d2a6f49b81c4857ba20bb236920932a7c34392c63e70d0882099a`, exporter `8da82299d3b2b2b426bdace5c129a412672cacaaafba14c821fff35bcd9a2441`, emitted endpoint deck `e8f7376817daa1e3ac0b7d5f85c52b16115c2cef39291486d1800e0e847e0aff`, and ghost-diagnostic known answer `442db5b4bb39002882443ba716dfe37650d69c26c8ce823261bfffc2d7806e17`.

The preflight producer SHA-256 is
`c1f676b4dd3500f4886e27dd97edf38f9dd94eb5ee6a61d7de330aeaee16be1a`; the
verified readiness report SHA-256 is
`edcc2fbc8adddfab44e8419db8b297df4c8f6f6a11e905523d1bcb60102d84f7`. No raw
response vector was copied into this packet. Parent authorization is required
before either body is factored or solved.
