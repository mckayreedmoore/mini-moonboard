# Current group-action method — attempt06

Status: offline method-only hardening based on the replayed maintained attempt05 bytes. Attempt05 and earlier attempt packages remain unchanged.

This revision adds a public positive-path regression showing that a finite row axis with an overflowing raw norm still produces the expected straight-row geometry when its fastener centers, applied load, and grain directions align. It also makes canonical JSON hashing return `None` when recursive validation or JSON encoding exceeds Python's recursion capacity, so the public evaluator fails closed as `pending`; and it distinguishes JSON scalar types when reporting changed sensitivity paths (for example, integer `1` versus boolean `true`). A contract that omits the scalar-type change remains pending.

The patch replays without fuzz from the included attempt05 base files. The focused group-action test file passes. Fresh independent correctness, test, and architecture reviews are pending. This remains method-only: no candidate values, resistance, capacity, or criterion dispositions. No solver, Docker, current-joint run, geometry change, or criteria method-map change was performed.
