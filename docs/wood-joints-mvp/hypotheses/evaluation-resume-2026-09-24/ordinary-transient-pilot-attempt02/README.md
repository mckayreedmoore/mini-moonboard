# First executed gauge-free motion pilot

The parent launched this exact frozen input with the pinned CalculiX 2.21
binary, one solver thread, a two-CPU quota, 10 GiB memory and a 600 s runtime
bound. See execution.json for the authoritative terminal or running state.
The source geometry, material, 35 contact pairs and provisional nut coupling
come from native-preflight-attempt04. The six static gauge restraints are
explicitly omitted, and a balanced paired N load follows the sampled cubic
1 N / 0.1 s ramp. The requested endpoint is 0.025 s (0.15625 N).

The first actual increment is 0.0005 s. The generic parser warning that the
initial increment is ignored does not match this observed implicit NLGEOM
path. The system has 334,914 equations, six more than the gauged preflight.
Initial iteration output reports a maximum displacement increment of
1.691064e-8 mm. Contact-element counts change strongly and continue varying
around 21,000 after the initial 93,540; this prevents interpreting the trial
iterate as a converged motion. The native convergence routine requires a
stable active contact count as well as force and correction conditions.
No convergence tolerance, physical support, preload or friction was changed.

The .dat displacement output is required before the bounded-motion monitor
can evaluate its first complete sample. The runtime bound remains effective
while the solver is iterating without a converged sample. Trial iteration
logs are preserved as numerical diagnostics, not joint displacement evidence.
No loaded-response, stiffness, resistance, or candidate acceptance follows
from this attempt's input preparation or trial iterations.

Attempt01 was not executed; it preserved an earlier include order. Attempt03
is separately frozen with a larger initial time increment while retaining
adaptive cutbacks, with unchanged physical and load artifacts.
