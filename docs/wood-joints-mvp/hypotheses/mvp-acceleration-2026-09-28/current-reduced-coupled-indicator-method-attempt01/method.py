"""Borrowed linear indicators for source-bound reduced equilibrium.

Construction only. Callers own budgets, source binding, branch/nullspace
validation, episode references, and physical-response acceptance.
"""

def build(H, D, e, W, laws, floor_cells, excluded_floor_masks=(), time_limit=3.0):
    from pyscipopt import Model, quicksum

    n, nr = len(e), len(W)
    assert len(H) == n and len(D) == n and len(laws) == n
    assert all(len(row) == n for row in H)
    assert all(len(row) == nr for row in D)
    normal_rows = [cell['normal_row'] for cell in floor_cells]
    tangent_rows = [row for cell in floor_cells
                    for row, _ in cell['tangent_rows_and_references']]
    assert len(set(normal_rows)) == len(normal_rows)
    assert len(set(tangent_rows)) == len(tangent_rows)
    assert set(tangent_rows) == {i for i, law in enumerate(laws) if law['kind'] == 'tangent'}
    model = Model()
    model.hideOutput()
    model.setParam('limits/time', time_limit)
    model.setParam('parallel/maxnthreads', 1)
    model.setParam('numerics/feastol', 1e-9)
    q = [model.addVar(name=f'q_{i}', lb=None, ub=None) for i in range(n)]
    f = [model.addVar(name=f'f_{i}', lb=None, ub=None) for i in range(n)]
    a = [model.addVar(name=f'a_{j}', lb=None, ub=None) for j in range(nr)]
    modes = {}

    def imply(expr, mode, active, name):
        model.addConsIndicator(expr <= 0, binvar=mode, activeone=active, name=name)

    def equal(expr, mode, active, name):
        imply(expr, mode, active, name+'_upper')
        imply(-expr, mode, active, name+'_lower')

    for i in range(n):
        expression = q[i] + quicksum(float(H[i][j])*f[j] for j in range(n) if H[i][j])
        expression -= quicksum(float(D[i][j])*a[j] for j in range(nr) if D[i][j])
        model.addCons(expression == float(e[i]), name=f'compatibility_{i}')
    for j in range(nr):
        model.addCons(quicksum(float(D[i][j])*f[i] for i in range(n) if D[i][j])
                      == float(W[j]), name=f'raw_body_wrench_{j}')
    for i, law in enumerate(laws):
        kind = law['kind']
        if kind == 'tangent':
            continue
        k = float(law['k'])
        assert k > 0
        if 'domain_mm' in law:
            lo, hi = law['domain_mm']
            model.addCons(q[i] >= lo)
            model.addCons(q[i] <= hi)
        if kind == 'bilateral':
            model.addCons(f[i] == k*q[i], name=f'bilateral_{i}')
        else:
            assert kind == 'unilateral'
            mode = modes[i] = model.addVar(name=f'bearing_{i}', vtype='B')
            imply(-q[i], mode, True, f'bearing_q_{i}')
            equal(f[i]-k*q[i], mode, True, f'bearing_law_{i}')
            imply(-f[i], mode, True, f'bearing_force_{i}')
            imply(q[i], mode, False, f'open_q_{i}')
            equal(f[i], mode, False, f'open_force_{i}')
    floor_modes = []
    for cell in floor_cells:
        mode = modes[cell['normal_row']]
        floor_modes.append(mode)
        for row, reference in cell['tangent_rows_and_references']:
            assert laws[row]['kind'] == 'tangent'
            equal(q[row]-float(reference), mode, True, f'held_reference_{row}')
            equal(f[row], mode, False, f'released_tangent_{row}')
    for j, mask in enumerate(excluded_floor_masks):
        assert len(mask) == len(floor_modes)
        model.addCons(quicksum(1-mode if held else mode
                              for held, mode in zip(mask, floor_modes)) >= 1,
                      name=f'excluded_floor_episode_{j}')
    return model, q, f, a, floor_modes
