# Coupled contact indicator-selector fixture — attempt01

## Bounded result

PySCIPOpt 6.2.0 with its bundled SCIP 10.0.2 solved the pinned small linear
fixtures using binary indicators and no caller-supplied finite big-M or
displacement/force caps. The replay enumerates admissible closed/open masks,
excludes each found mask with a no-good row, and independently checks the
simultaneous equilibrium and each branch law. The machine-readable cases and
answers are in [known-answer.json](known-answer.json); the replay is
[select_states.py](select_states.py).

The observed results are:

| Fixture | Result | Observed state |
| --- | --- | --- |
| One-cell event at zero normal and tangent force | `AMBIGUOUS_ZERO_BOUNDARY_MASKS` | Open and closed masks both return `t=-2 mm`, `q=T=N=0` |
| One-cell held state with supplied `t_ref=-2 mm` | `ONE_ADMISSIBLE_MASK` | `t=-2 mm`, `q=0.25 mm`, `T=-0.25 N`, `N=0.5 N` |
| Parent one-cell fixed-reference counterexample | `NO_ADMISSIBLE_STATE` | SCIP proves infeasible across both masks |
| Mirrored parent one-cell load | `MULTIPLE_ADMISSIBLE_MASKS` | Open and closed states both pass |
| Four supplied two-cell coupled stages | `ONE_ADMISSIBLE_MASK` each | The selected mask and state match each source hand-answer oracle |

All binary masks were exhausted for these one- and two-contact cases: either
every possible mask was returned once or the model with all found masks
excluded was proven infeasible. This is a tiny-fixture result. It does not
predict the cost or behavior of a 100-contact search.

## Formulation and coordinate signs

For each contact `i`, the model has a binary `closed_i`, a tangential
displacement `t_i`, signed compression coordinate `q_i`, signed tangent force
`T_i`, and normal force `N_i`. Every continuous variable is created with
`lb=None, ub=None`. Simultaneous equilibrium for all degrees of freedom is
`K u - C f = W`, where `C` is source-pinned and records the sign convention of
the supplied fixture.

The branches are explicit:

- `closed_i = 1`: `q_i >= 0`, `N_i = k q_i >= 0`, and `t_i = t_ref_i`; `T_i`
  remains signed and unbounded.
- `closed_i = 0`: `q_i <= 0`, `N_i = 0`, and `T_i = 0`.

Each equality is encoded as two linear indicator inequalities. The PySCIPOpt
API supports indicators active at either binary value. SCIP documents an
indicator as a one-way implication and describes its indicator handler using a
slack variable and SOS1 constraint, so the script explicitly gives both
branches and never assumes an implication is an equivalence. No big-M
coefficient or finite bound is chosen by this fixture. The solver can still
apply its internal presolve and separation methods.

The event-reference fixture already uses positive `q` for compression and has
`K u + [T,N] = W`; its `C` entries are therefore `[-1,-1]` in the displayed
`K u - C f = W` form. The structural-coupling source uses positive gap `z` and
`W - K u + f = 0`. There the script applies `D=diag(1,-1,...)`, sets
`q=-z`, `K'=DKD`, `W'=DW`, and `C'=D`, retaining positive `N` while making
positive `q` the compression direction. This same transform is applied to the
parent's one-cell no-state/two-state counterexamples.

The event and two-cell stage references are supplied from their exact analytic
oracles. The selector does not find an event, capture or update a reference,
advance an episode, or claim that a prescribed stage sequence is a physically
available load path. At zero extension, both weak-sign branches can be valid;
the checker recognizes coincident `q=N=T=0` states with different masks as
`AMBIGUOUS_ZERO_BOUNDARY_MASKS` instead of silently choosing one.

## Sources and replay

Input JSON, fixture producers and the one-cell parent counterexample are
SHA-256 pinned in the result. The two-cell matrices, loads, references and
expected states come from the existing owner fixture; no source fixture is
edited here.

The official [PySCIPOpt model API](https://pyscipopt.readthedocs.io/en/stable/api/model.html)
documents `addConsIndicator`, the `activeone` selector and `lb=None` /
`ub=None` for unbounded variables. The official [SCIP indicator handler
documentation](https://www.scipopt.org/doc-10.0.0/html/cons_indicator.h_source.php)
states that an indicator is an implication, not an equivalence, and describes
its slack/SOS1 implementation. PySCIPOpt's [model tutorial](https://pyscipopt.readthedocs.io/en/latest/tutorials/model.html)
documents setting `limits/time`; the [installation guide](https://pyscipopt.readthedocs.io/en/stable/install.html)
documents Linux x86_64 wheels.

The replay uses an ephemeral environment and does not change the project
dependencies:

```sh
uv run --no-project --with pyscipopt==6.2.0 python \
  docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-coupled-indicator-selector-fixture-attempt01/select_states.py --verify
```

The script has a 30-second suite wall budget and a three-second limit per SCIP
call. An unproven solver status or exhausted budget is recorded as
`BUDGET_OR_SOLVER_STOP`; it cannot become a uniqueness or infeasibility claim.
The separate zero-budget behavior check exercises that stop path without
rewriting the known answer:

```sh
uv run --no-project --with pyscipopt==6.2.0 python \
  docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-coupled-indicator-selector-fixture-attempt01/select_states.py --exercise-zero-budget-stop
```

It must report `PASS_EXPLICIT_ZERO_BUDGET_STOP_NO_COMPLETENESS_CLAIM` and
records `global_wall_budget_exhausted` with no states and no completeness
claim. The source fixtures are small positive-definite mathematical carriers,
not a frame or floor operator. Operator retrieval/reduction is separately
owned.

No CalculiX solve, geometry change, gravity/frame compatibility conclusion,
current-frame state, mechanics acceptance, or design qualification is made.
