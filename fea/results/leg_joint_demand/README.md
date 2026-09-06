# Retained-output leg demand evidence

`successful.tar.gz` preserves the unchanged contents of local extraction
`fea/generated/leg-joint-demand-iwk1l84z`: authenticated input, leg element
ownership and weights, all 32 reported increments, source snapshots and the
Gmsh integration log. Archive members are rooted directly at `input.json`,
`integration.json`, `report.json`, `integration.log` and `launch_sources/`.

`failed-launch.tar.gz` preserves the prior
`fea/generated/leg-joint-demand-oqh1pq63` attempt. Its container command used
unavailable `python`; it did not integrate or solve. The successful attempt
uses `python3`. No original evidence is replaced by the corrected command.

This is aggregate equilibrium recovery from the original undrilled, bonded
frame, **not a new FEA solve or candidate/bolt/ply capacity result**. The
[analysis and limitations](../../../docs/leg-joint-demand.md) identify force
directions, moment reference locations and the seven retained intermediate
global diagnostic failures.

Archive SHA-256 identities:

- `successful.tar.gz`: `44babcb9329b5e6cc87c4946a76dad241ea779de73f8d79502569120d3190e43`
- `failed-launch.tar.gz`: `7479179de137ae2088758ce347ab01d170ac22e4bbc0e1827f60c84467af90f7`

Five focused tests pass, including an offline replay of every reported vector
and flag using the retained archive and weights. The final independent
correctness, testing and architecture/publication review pass found no
substantial remaining findings. Replay does not rerun Gmsh or CalculiX and does
not convert the conditional baseline demand into structural approval.
