# Parent execution of the first-state mass and moment diagnostic

The parent ran the independently reviewed producer against the frozen
accepted state 1:1 at 0.0005 s. The [execution](execution.json) completed
with return code zero in 34.46 seconds and unchanged producer source.
[result.json](result.json) has SHA-256
`3eefb2fb2bbd7f22d9a8c735e6ca63c30f8b993dbf9d2491d5e6689db04ebf95`.

The prior host invocation failed before integration because `.venv` does not
include Gmsh. This retry uses the existing Gmsh 4.12.1 image
`sha256:37671083a88ded305c4fcd83960a767dad4c2acb480976cb75fab5df261e2646`
with the project's NumPy 2.5.2 mounted read-only. Python is 3.12.3. The image
and imports were checked before launch; no dependency or input was changed.
The native trajectory was already stopped and its container removed before
this serialized calculation. The exact command and mounts are in the record.

The model's positive-density mass integrates to 0.0117756010093 tonnes,
with four zero-density nut carriers kept distinct. This is the isolated
diagnostic assembly, not the whole board's weight. The reported global force
residual is approximately `[-4.95e-14, 9.78e-13, 2.08e-14] N`.

The global origin-moment residual is
`[-4.85061e-10, -2.35644e-11, 4.23486e-11] N mm`. These components exceed
the narrow conditional output-token bounds
`[2.54520e-13, 8.78279e-14, 1.02216e-13] N mm`.
The bounds explicitly exclude mass integration/assembly error, acceleration
and recovered-multiplier uncertainty, and native solver/model error. No
equilibrium pass follows from the small absolute residual. The difference
requires interpretation and independent review before this result is used
as equilibrium evidence.

The captured source remains a nonterminal first-state prefix, even though
the later trajectory has now been stopped. The output correctly keeps
whole-horizon, model and mechanical acceptance false. Individual-body rows
also remain component partitions because generated rigid-carrier reactions
are not included. No contact-event-state reconstruction is contained here.
