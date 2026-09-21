# PB02 provisional component actions

The [reproducible report](../../scripts/simple_center_provisional_component_actions.py)
turns each solved PB02 spring-reaction record into per-bolt, per-face, per-interface, and
per-body actions. It uses the `ligament_priority` variant and source fingerprint
`4303388fad70e89ea4a65741e0fa2af38ab7d1d526f3af0be8ac0c9ac46de721`.

This is an interpretation of authenticated old-duty trials. It is not a current PB02
design-demand report, and the source set does not contain `a12-forward`.

## Force and moment conventions

For every compatibility row, `signed_reaction_n * direction` is the force on the row's
`second` body. Its negative is the equal-and-opposite force on the `first` body.

Each bolt combines its two bilateral shear rows into one signed three-dimensional shear
vector and magnitude. Its separate axial row is reported as tension only: an active row
has a nonnegative tension magnitude and an open row reports zero axial force. The report
also gives the vector sum of that same bolt's simultaneous shear and axial forces. It does
not combine maxima from different records.

Each interface face retains four compression-only samples. Their forces are summed into a
face resultant, and their moments are summed about that interface's center from
`EDGES[edge][4]`. The complete interface wrench adds the bolt and face actions and is
reported independently on both bodies.

The body-equilibrium reconstruction uses a different moment reference: every internal and
external body moment is taken about the shared model `ORIGIN`,
`[140, -140, 270] mm`. An interface-center moment therefore must be translated before it
can be compared with an `ORIGIN` moment. The two values are not interchangeable.

## Executed output

The executable report produces 50 unique records: five historical cases crossed with ten
stiffness scenarios.

- Cases: `a1-rear`, `a12-left`, `a12-rear`, `k12-rear`, and `k12-right`.
- Scenarios: `reference`, three soft cases, three stiff cases, two contrast cases, and the
  formula-anchored lateral sensitivity.
- Maximum reconstructed body force residual: `5.41812e-8 N`.
- Maximum reconstructed body moment residual: `1.45331e-5 N-mm`.
- Maximum equal-and-opposite interface residual: zero in the emitted results.

All 50 reconstructed body-equilibrium checks pass the report's `1e-5 N` force and
`1e-3 N-mm` moment tolerances.

For example, the `a12-rear/reference` record uses `10,000 N/mm` for bolt shear, bolt axial
tension, and total face contact; each of the four face samples receives `2,500 N/mm`.
Its maximum body residuals are `1.74303e-10 N` and `4.24770e-8 N-mm`. On the
`post_block` interface, its two bolts carry simultaneous shear magnitudes of `779.241 N`
and `1,123.279 N`, with axial tensions of `1,778.417 N` and `5,034.436 N`. Two of the four
face samples are active. These are one record's compatible reactions, not strengths or
design demands.

## Serial path groups

The report preserves exactly three ordered groups:

1. `header_to_post`: `post_block`, then `block_header`.
2. `header_to_principal`: `header_principal_block`, then
   `principal_block_principal`.
3. `return_path`: `principal_upright_block`, then `upright_rear_block`, then
   `rear_block_post`.

These groups identify interfaces that participate in the same serial load path. Their
wrenches are not summed as capacity. Adding them would double-count internal transfers,
mix actions taken at different interfaces and moment centers, and obscure the equilibrium
of the intervening bodies. Capacity must instead be checked at each applicable interface
and component using its simultaneous action from one case/scenario record.

## Claim boundary

The source actions are authenticated historical duties used to exercise the developmental
topology. They omit `a12-forward` and do not establish current PB02 loads. No bolt, wood,
washer, contact, block, group, or combined resistance is evaluated here. The report does
not select G1 and is not a structural, drilling, fabrication, purchasing, or construction
release.
