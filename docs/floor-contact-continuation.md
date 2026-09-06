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
trial completed all three solver steps normally in 585.067 seconds; 0.5 is
not measured floor data. Its released-gravity state has a 4.892 Nmm moment
residual, still above the same 1 Nmm limit. Increasing assumed friction changes
the contact state and reduces that residual; it does not close the audit.

No complete, equilibrium-audited free-board solution is accepted. No geometry
or material-strength recommendation follows from these numerical trials alone.

## Completed load step: moment-transfer discrepancy

The [μ=0.5 report and raw evidence](../fea/results/floor_contact_continuation/full-increment-mu0p5/report.json)
retain normal solver completion **and** the failed production audit. A separate
[independent audit of all three endpoints](../fea/results/floor_contact_continuation/full-increment-mu0p5/independent_audit.json)
checks complete contact statistics, not only convergence messages.

| μ=0.5 endpoint | Ground-reaction-based moment residual about X, Nmm | Wood-side contact-force-based moment residual about X, Nmm |
| --- | ---: | ---: |
| Released gravity | 4.892 | -0.031 |
| Released gravity + 1,200 N | 256.555 | 0.278 |

All three wood-side residual components in the loaded state are below 1 Nmm,
but the **ground-based global audit still fails**. Equal contact forces alone
do not establish correct moment transfer. The loaded kicker's wood/ground
contact moment difference is about -269.136 Nmm, compared with a propagated
printing uncertainty of about 0.040 Nmm; printing precision does not explain it.
All patch force comparisons agree within their printed precision. The loaded
global force residual is below 0.000071 N and released guide components below
0.000000065 N, so missing net force or retained guides do not explain this gap.

Active integration-point pressure and Coulomb checks pass within printed
precision. The loaded kicker is again close to the assumed friction limit
(aggregate utilization about 0.99991). The calculated maximum displacement is
1.234 mm, and maximum displacement among the five load nodes is 1.098 mm.
These are **rejected-model diagnostics**, not validated deflection, bearing
pressure or strength predictions. Missing/inactive regions and mesh/history
sensitivity remain additional gates.

The supported diagnosis is a contact-interface moment-transfer discrepancy.
Frozen within-increment face matching/projections are a plausible mechanism,
not a proven solver implementation bug. The exact-version
[CalculiX 2.21 manual](https://www.dhondt.de/ccx_2.21.htm.tar.bz2)
(nodes 140 and 142) describes the face-to-face matching and contact stiffness
used here. Wood-side balance must not replace the ground-based acceptance test.

## Refined release/loading: gravity passes, loaded moment still fails

The [0.1-increment run](../fea/results/floor_contact_continuation/free-increment0p1-mu0p5/report.json)
finished normally in 1,405.2 seconds. It retains the full guided preload, then
uses ten increments for released gravity and ten for the original 1.2 kN load.
Geometry, μ=0.5, contact slopes and complete guide removal are unchanged.
The [independent endpoint audit](../fea/results/floor_contact_continuation/free-increment0p1-mu0p5/independent_audit.json)
and original raw outputs are preserved with the exact launch-source snapshot.

| Maximum absolute ground-based moment residual | Full-step increments | Refined release/load increments | Unchanged limit |
| --- | ---: | ---: | ---: |
| Released gravity | 4.8925 Nmm | 0.07263 Nmm | 1 Nmm |
| Full 1.2 kN load | 256.5547 Nmm | 96.0176 Nmm | 1 Nmm |

Released gravity now passes the global force/moment check; the loaded state
still fails. Loaded force residual components remain below 0.000071 N and
released guide XY reactions below 1.5e-10 N. Wood-side CF moment components
remain below 0.096 Nmm, but the kicker's CF-versus-ground Mx discrepancy is
−98.4103 Nmm against about 0.03965 Nmm of propagated printing uncertainty.
The improvement supports increment sensitivity, not proof of the exact source
mechanism or acceptance of the loaded solution.

All 69 printed active integration points satisfy compression, the normal law,
and the assumed Coulomb bound within propagated print precision. Missing active
faces are not thereby proven open. Kicker aggregate friction utilization is
approximately 1.0000 at the assumed μ=0.5. Maximum nodal displacement is
1.23428 mm, almost unchanged from the full-step result; agreement in displacement
does not cancel the failed moment audit. These are rejected-model diagnostics,
not verified deflection, contact pressure or capacity predictions.

## Next numerical step

1. Retain the demonstrated guided preload, same geometry, friction assumption,
   contact slopes and complete guide release. Reduce increment sizes specifically
   during free gravity and climbing loading so contact matching refreshes more
   frequently. The first refinement above improves but does not resolve loading;
   keep the 1 Nmm moment limit unchanged.
2. Compare wood/ground force and moment transfer across increment refinements,
   alongside local pressure, friction and actual gaps. If the discrepancy
   persists, compare a documented mortar formulation on the actual-foot coupon
   before transferring it to the whole frame.
3. Only after an audited unanchored baseline exists, run central and A12/K12
   asymmetric loading and broader friction/mesh/history sensitivities. The
   current data do not justify resizing the timber or declaring a safe load.

## Verification

The separate `--free-increment 0.1` experiment keeps the successful full guided
preload and caps both released-gravity and climbing-load increments at 0.1.
It changes neither the contact law nor the released boundaries. The option is
exclusive with `--full-increment`; fractions must be finite in `[0.005, 1]`.
The lower bound follows the existing 200-increment limit, and 0.005 leaves no
headroom for cutbacks. This is a numerical sensitivity, not a convergence promise.
Its launch snapshot is preserved separately from later runner validation edits.

Independent correctness, testing and architecture reviews are complete for the
runner and the first two published trials. Confirmed fixes prevent an empty
load-node list from masquerading as a 1,200 N load and reject invalid numerical
contexts. Regression checks exercise deformed gravity, guide and load moments,
guide removal, force/moment perturbations and friction sensitivities. Archived
decks and outputs are replayed without requiring generated source files.
A solver-complete but audit-rejected run remains valid *failure evidence*; its
test must reproduce the rejection, not demand a passing physical result.

Final publication checks passed 173 related tests, with one optional Gmsh
coupon replay skipped on the host (its equivalent was separately verified in
the pinned Docker image). The 51 continuation tests include all three archived
trials and reproduce the μ=0.5 rejection. Independent correctness and testing
reviews of the final publication found no substantial remaining issues.
