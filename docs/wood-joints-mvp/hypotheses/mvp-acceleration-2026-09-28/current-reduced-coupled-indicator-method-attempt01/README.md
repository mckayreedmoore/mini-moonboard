# Reduced coupled source-law indicator method

This parent-owned construction reuses pinned PySCIPOpt 6.2.0 linear indicators for q=D*a+e-H*f and raw body equilibrium D.T*f=W. Bilateral rows use f=k*q. Unilateral rows use one coupled branch choice for f=k*q with q>=0 or f=0 with q<=0. Each floor cell shares its normal branch with both tangent rows: held rows use supplied episode references; open rows carry zero tangent force. Finite native spring-table domains can be retained explicitly.

No floor mask is guessed. No unilateral branch is selected independently of equilibrium. No spring, body or reaction is added. Nonfloor zero-force branch bits are bookkeeping, while floor episode choices are separately enumerated by no-good constraints. Solver timeout, multiple physical floor branches and zero-force/event ambiguity remain caller stops, not permission to choose a favorable branch.

The isolated producer reproduces all eight existing coupled toy oracles, including no-state, multiple-state, zero-boundary and nonzero-reference cases, in reduced compliance coordinates. Two additional signed raw-body-wrench oracles test D/W and bilateral forces. Those fixtures have no free-body gauge and do not validate a full-frame branch nullspace or initial event history.

Replay: `OPENBLAS_NUM_THREADS=1 uv run --no-project --with pyscipopt==6.2.0 --with numpy==2.5.2 python docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-reduced-coupled-indicator-method-attempt01/verify_method.py --verify`.

This does not run the frame or a native solver, capture any event, accept a support state, or qualify a joint. The parent must bind reviewed zero-load geometry/initial gaps, exact signed references, all gravity, original source laws, branch nullspace/load compatibility, numerical budgets and independent physical checks before an actual directional solve.

The indicator API and its equality-as-two-inequalities convention are reused from [the pinned known-answer selector](../current-coupled-indicator-selector-fixture-attempt01/), which records official solver documentation and scope limits. This is a reduced algebraic coupling adapter to that borrowed solver, not a replacement finite-element engine.
