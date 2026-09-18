# Coupled whole-frame gusset-release trial

The subsequent [leg/rim release](coupled-leg-release.md) also removes the bonded
leg-to-rim and leg-to-panel paths. Use that follow-up for conditional leg-bolt
transfers; the results below deliberately preserve bonded legs as a comparison.

This trial allows the surrounding frame to redistribute deformation when the
gusset ties are released. It supersedes the frozen-parent-motion limitation of
the [isolated connector trial](gusset-connector-trial.md) for this specific
interface comparison. It is still not physical joint qualification.

## Exact change from the bonded parent

The accepted current-wide 40 mm solid mesh, material, applied hold nodes and
fixed-floor conditions are retained. The 830 shared gusset nodes are duplicated
at identical coordinates; only the corresponding gusset element connectivity
changes. Neither gusset shares solid nodes with any other member afterward.
All element coordinates, volumes and the other members' element connectivity
remain unchanged. No new CAD or manufacturing variant is selected by this trial.

Eight connector points lie at the actual bolt-axis intersections with their
proper rim/post interfaces. Each side of every connector uses the verified
quadratic face interpolation. Three native translational springs per connector
join parent and gusset point DOFs; neither endpoint is prescribed or grounded.
There are 48 point-interpolation equations and 24 springs in each deck.
No equivalent frozen-parent load is applied in this coupled model.

Only original floor nodes have prescribed zero displacement. The frame receives
nine 1,000 N Cartesian basis loads: X, Y and −Z at each of A12, K12 and F6.
The planned stiffness sweep is 100, 1,000 and 10,000 N/mm per connector axis.
These are numerical parameters, not measured bolt properties or bounds on them.

## Predeclared numerical acceptance

- Exactly nine complete output endpoints, with every selected displacement and
  floor reaction node present and finite.
- Global force residual ≤ 0.1 N and global moment residual ≤ 1 N·mm.
- Each gusset's connector force residual ≤ 0.02 N and moment residual ≤ 5 N·mm.
- Floor and interpolated-point displacement constraints within 1e-6 mm.
- Positive collocated load work, no smaller than the bonded parent's work
  beyond a 0.01 N·mm print-precision tolerance. Releasing ties must not make
  this unchanged linear model artificially stiffer.

The replay tests also check non-increasing collocated compliance with increasing
positive spring stiffness. The expected relationship is not a material-strength
criterion. Connector forces are `k*(u_parent_point-u_gusset_point)` on the gusset;
the force on the parent point is opposite.

After a basis set passes, the existing scenario generator combines signed
vectors for 150/200/250/300 lb, one/two times weight, and either no horizontal
force or 300 N at eight azimuths. Each stiffness has 216 derived scenarios;
they are not independently solved nonlinear load cases.

## Limits that remain important

Other member interfaces remain ideally bonded, including leg plies and
leg-to-rim/upper-panel interfaces. Rim, post and header load sharing outside the
released gusset interfaces is not changed. The removed gusset/header bond is
not replaced by unilateral bearing contact in this trial. Interpenetration,
opening/recontact, friction and washer action are not evaluated. Thus the
remaining bonds may still bypass physical fasteners.

The wood remains isotropic E = 7,000 MPa, Poisson ratio 0.3. The floor remains
fixed XYZ, including the kicker, with no gravity. This is not the actual
unanchored floor response. Springs are bilateral and equally stiff in all
three axes; real axial, lateral, gap and yielding behavior are not established.
Point forces do not resolve bore bearing, washer pressure, splitting, block
shear or mesh-converged local stress. Do not use the result as a bolt allowable,
an actual demand envelope or a frame rating.

The generator retains its source hashes, exact decks and native output. A solver
error or failed numerical gate prevents scenario publication for that basis set;
attempt files remain available for diagnosis. This document specifies the trial;
results and recommendations follow only after its output is verified.

## Verified result

All three native jobs completed successfully: 27 solved bases and 648 derived
scenarios. Every predeclared gate passed. Maximum basis global residuals were
0.000127 N and 0.08204 N·mm; maximum gusset residuals were 0.0000601 N and
0.07308 N·mm. Maximum displacement-constraint error was below 8.6e-9 mm.
The archive replay also passed the stiffness/compliance ordering check.

| Assumed stiffness per axis | Largest connector resultant, nine bases | Largest connector resultant, 216 combinations | Largest load-work ratio to bonded parent |
| --- | ---: | ---: | ---: |
| 100 N/mm | 0.2426 N | 0.6785 N | 1.04340 |
| 1,000 N/mm | 2.3407 N | 6.5587 N | 1.04313 |
| 10,000 N/mm | 18.2249 N | 50.3075 N | 1.04123 |

For comparison, the isolated frozen-parent trial's largest basis force at
10,000 N/mm was 13.5673 N. The coupled result is about 34% larger; the one-way
result was not a substitute for frame redistribution. Releasing the gusset ties
also increases the relevant collocated compliance by up to approximately 4.34%.
Increasing positive connector stiffness decreases each collocated compliance,
as expected for this unchanged linear model.

Maximum loaded-hold displacement magnitude over the combinations is 2.49675 mm
at 100 N/mm, 2.49670 mm at 1,000 N/mm and 2.49638 mm at 10,000 N/mm. These are
loaded-node values, not a search for the largest displacement anywhere in the
frame, and remain subject to all the stated material and boundary assumptions.

At the highest **tested**, not upper-bound, stiffness:

| Climber comparison mass | Maximum connector resultant over the corresponding combinations |
| --- | ---: |
| 150 lb | 27.7459 N |
| 200 lb | 35.2656 N |
| 250 lb | 42.7863 N |
| 300 lb sensitivity | 50.3075 N |

Each row includes the one/two-times-weight and horizontal-force cases defined
above. These are not rated user weights, impact-test results or simultaneous
component maxima. Every signed connector vector remains in the archive.

## Design disposition and remaining work

This establishes conditional asymmetric connector demands in a coupled frame
with the explicitly stated spring/bond/floor assumptions. It does **not** prove
the gusset adequate: other ideal bonds still bypass real joints, the stiffness
range is not calibrated or bounding, and axial/washer, wood failure and contact
behavior remain unresolved. Do not divide these numbers by an unadjusted bolt
yield reference and call the quotient a safety factor.

Retain the current gusset dimensions and hardware for inspection; this trial
alone warrants neither reduction nor enlargement. The next model change should
address the remaining physical base/leg joint paths and permissible bearing,
with an applicable connector stiffness/resistance basis. Keep the open end-angle
installation and panel-insert gates separate. The reported result is not a
reason to restart generic lumber-depth comparisons.

The [portable native archive](../fea/results/coupled-gussets.tar.gz) contains the
three exact decks, solver outputs/logs, source hashes, duplication/point maps,
all basis results and all scenario vectors. Tests reconstruct the released
mesh and decks, replay output and combinations, and reject incomplete output.

```sh
uv run pytest -q tests/test_coupled_gussets.py tests/test_gusset_connector_trial.py tests/test_gusset_recovery.py
```

Independent correctness, testing and architecture/package-consistency reviews
found no substantial issues in the completed implementation and native archive.
The broader connection/recovery regression passed 41 tests; Ruff and
`git diff --check` were clean. Reviewers independently checked reported archive
counts and numerical maxima without rerunning heavy solves. This checkpoint
does not constitute professional structural approval.
