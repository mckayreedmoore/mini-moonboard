# Current group-action method — attempt07

Status: offline method-only hardening based on the replayed maintained attempt06 bytes. Attempt06 and earlier attempt packages and reviews remain unchanged.

This revision closes the attempt06 signed-zero sensitivity-path finding. Leaf comparisons now use the module's canonical JSON byte representation, so changes such as integer `1` to boolean `true` and floating-point `-0.0` to `0.0` are included in the exact changed-path list. The public sensitivity regression reports the signed-zero path when declared and returns `pending` when that path is omitted.

The attempt06 and attempt07 patches replay without fuzz from their included pinned bases. The focused group-action test file passes. Fresh independent correctness, test, and architecture reviews are pending. This remains method-only: no candidate values, resistance, capacity, or criterion dispositions. No solver, Docker, current-joint run, geometry change, or criteria method-map change was performed.
