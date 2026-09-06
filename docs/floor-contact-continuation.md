# Temporary-guided full-frame contact initialization

This bounded experiment tests whether establishing gravity contact before
releasing lateral freedom changes the original zero-accepted-increment result.
It retains the frozen 60 mm frame, μ=0.3, normal penalty 10,000 N/mm³,
tangential penalty 100 N/mm³, original static controls, and original load patch.

1. Gravity preload fixes x/y at all 610 actual floor-contact nodes; z stays free.
2. A first `*BOUNDARY,OP=NEW` card removes every prior displacement constraint
   and repeats only the fixed ground-node constraints. Gravity continues with
   the entire timber frame unpinned.
3. The original 1,200 N downward load is added with the same released frame.

CalculiX 2.21 [`*BOUNDARY` documentation](https://www.dhondt.de/ccx_2.21.htm.tar.bz2)
(manual node219) says OP=NEW removes
previously prescribed displacements, and only the first boundary card of the
step controls that operation. The generated second step follows that rule.
There are no final timber pins, guides, damping, or springs. The guided first
step alone cannot be an accepted board solution.

The runner records exact input/deck/source hashes before launch in a fresh
`fea/generated/continuation-xy-*` directory. It requests guide reactions,
all timber displacements, all ground reactions, and `*CONTACT PRINT` local
CDIS/CSTR plus patch CF/CFN/CFS outputs. The three-step audit includes temporary
guide reactions only in step 1 and verifies complete output, deformed force and
moment balance, and necessary aggregate floor bounds at all three endpoints.
Even successful completion still requires local contact and initialization-history
sensitivity checks before acceptance.

```sh
docker run --rm --user "$(id -u):$(id -g)" -e OMP_NUM_THREADS=2 \
  -v "$PWD:/work" mini-moonboard-fea:box-v1 \
  python3 -m fea.floor_contact_continuation --max-seconds 600
uv run pytest -q tests/test_floor_contact_continuation.py
```

The separate `--full-increment --max-seconds 900` sensitivity attempts each
whole step initially (`1,1,1e-6,1` instead of `0.05,1,1e-6,0.1`). Automatic
cutbacks remain enabled. It changes increment sizes, not physical loads,
restraints, friction or contact stiffness, and is recorded in a separate
directory with its own launch hashes. It is not a continuation of an accepted
free-board result.

The original-increment run stopped at 600.196 seconds after four accepted
guided increments, reaching 27.5% of gravity. It completed no full step and
never reached release or climbing load. Its
[report and archived solver evidence](../fea/results/floor_contact_continuation/original-increments/report.json)
retain that partial result and exact launch-source provenance.

The larger-increment μ=0.3 sensitivity completed guided gravity and reached
solver convergence at fully released gravity, but an independent audit finds
an approximately **89.268 Nmm deformed moment residual**, above the unchanged
1 Nmm acceptance limit. Force balance and zero released-guide reactions alone
do not make that state acceptable. It then stopped at its 900-second bound
during the climbing-load step, with no accepted climbing-load increment.
The [full-increment μ=0.3 report](../fea/results/floor_contact_continuation/full-increment-mu0p3/report.json)
and [independent endpoint audit](../fea/results/floor_contact_continuation/full-increment-mu0p3/independent_audit.json)
retain the exact DAT identity, calculations and rejection. Its timed-out DAT
contains incomplete final contact-force statistics: the left pair is complete,
the right pair is truncated, and kicker statistics are absent at time 2.
Complete force/displacement output permits the global rejection, but the
missing statistics prevent a complete pair-force/moment audit.
Active integration-point pressure and friction checks pass within printed
precision, but this does not override the global moment failure or establish
complete inactive-region contact validity.

In the guided configuration, the kicker's temporary lateral support was about
304 N versus about 228 N of aggregate friction capacity at μ=0.3. After release,
its computed aggregate friction utilization is about 0.99974. These are
conditional diagnostics of this state, not a certified minimum floor coefficient
or proof of instability. A separate `--full-increment --mu .5 --max-seconds 900`
trial is in progress to test friction sensitivity; 0.5 is not measured floor data.
Its released-gravity state also reaches solver convergence but has a 4.892 Nmm
moment residual, still above the same 1 Nmm limit. Increasing assumed friction
changes the contact state and reduces the residual; it does not close the audit.

No complete, equilibrium-audited free-board solution is accepted. No geometry
or material-strength recommendation follows from these numerical trials alone.

## Verification

Independent correctness, testing and architecture reviews are complete for the
runner and the first two published trials. Confirmed fixes prevent an empty
load-node list from masquerading as a 1,200 N load and reject invalid numerical
contexts. Regression checks exercise deformed gravity, guide and load moments,
guide removal, force/moment perturbations and friction sensitivities. Archived
decks and outputs are replayed without requiring generated source files.
A solver-complete but audit-rejected run remains valid *failure evidence*; its
test must reproduce the rejection, not demand a passing physical result.
