# Radial-gap unilateral engagement known-answer fixture, attempt 01

Status: prepared offline; no CalculiX or other native solver was run. The
fixture is isolated in this directory and does not change full-frame inputs or
shared solver code. Its exact small deck is [model.inp](model.inp), and the
branch-by-branch analytical answers are [expected_answers.json](expected_answers.json).

The fixture follows the active linear `SPRING2` branch and balanced
gap-reference loads used by `fea/current_response_run.py`, with isolated
auxiliary endpoint DOFs and force recovery described in the
[RF force-output handoff](../force-output-handoff.md). The pinned solver method
baseline is stock CalculiX 2.23. The existing
[reduced spring-method fixture](../reduced-static-methods-attempt02/README.md)
uses the 2.23 `SPRING2` semantics (manual section 6.2.41), and the
[RF-to-opening fixture](../rf-opening-known-answer-attempt02/README.md)
records the already checked auxiliary-node equation pattern. Those prior
results support the linear spring, MPC, and endpoint-output method; they do not
validate a radial gap state transition.

The new deck contains seven disconnected static branches in one input file:
an open interior point in a general direction; positive-side compression; a
positive-side unloading probe and its released open state; a reversed
displacement while the old positive side is still selected; an open transition
probe beyond the gap on the opposite side; and compression after selecting
that negative side. Each branch has a host-only support stiffness of 10,000
N/mm on each lateral axis. Active radial groups have equal 2,000 N/mm
components in DOFs 2 and 3 and a 0.5 mm radial gap. The physical radial plane
is global Y/Z solely to make signs visible.

For a stored unit normal `n`, gap radius `c`, stiffness `k`, and relative
endpoint displacement `r = u_second - u_first`, the active linear branch gives
`q_raw = k r`. The known reference term is `q_ref = k c n`, so the physical
force on the first endpoint is `q_phys = q_raw - q_ref`. The deck places the
balanced correction loads `-q_ref` on the first host and `+q_ref` on the second
host. The expected endpoint RF values remain the raw spring force: for
`q = k ΔU`, `RF_first = -q`, `RF_second = +q`, and the recovered value is
`(RF_second - RF_first)/2`. The correction loads do not act on those auxiliary
spring endpoint DOFs. The exact values, including the displacement and force
answers for every branch, are frozen in the JSON record.

The unloading probe deliberately evaluates the old positive-side linear
branch below the gap. Its `-400 N` corrected result is tension and marks that
branch for release; the following open branch carries zero radial force. The
reversed probe similarly makes the old-side branch inadmissible. The
intermediate open trial then selects the negative normal, which gives a
compressive `-500 N` physical force on the first endpoint when that branch is
activated. This models the active-set sequence as separate static states; it
does not claim CalculiX itself switches a radial spring unilaterally.

The displacement and force limits in the JSON are carried from the completed
reduced spring-method fixture: 2e-6 mm for host relative displacement and
0.002 N for recovered physical force. Endpoint force checks use the actual
printed-number half-last-place intervals for action/reaction and `k ΔU`, as in
the existing RF helper. The parent should freeze these exact inputs and review
the complete deck before any serialized native execution. Preparation alone
does not authorize launch.

The fixture establishes only known-answer method behavior for the listed
linear branches and force correction. It says nothing about a current joint,
contact stiffness calibration, frame stability, complete-joint resistance,
or a physical build.
