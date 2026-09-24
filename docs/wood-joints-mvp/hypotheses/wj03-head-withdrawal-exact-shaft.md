# WJ-03 exact coaxial shaft-withdrawal supplement

Diagnostic supplement to the preserved [coarse head-withdrawal report](wj03-head-withdrawal.md) for the compact outer third hypothesis. It replaces only the coarse shaft-withdrawal envelope analysis; it does not establish installation access, fabrication release, or structural acceptance.

- Supplement JSON SHA256: `58dc1e5c5d070835970c05875ea9f9cd5fac5e2fd30f6f4b3bb944713704f6a7`.
- Base report SHA256: `03cb0201b41b1a7dbded07bb5917301c078f698c950032c3524715583252b9f5`; preserved without overwrite.
- Producer SHA256: `706c3ddacb67e83419d8c8a9a049e24dd7d5cd5706647207bb767ad42c4b382c`.
- Focused test SHA256: `3d8187dd0811e62ee0211d0c47faf76a7744a091ec21938073aeca4a70680752`.
- Run: archive and all eight archived direct-source pins validated before materialization; one geometry materialization took 43.24 s; twenty exact shaft screens took 8.67 s; total 51.91 s.

## Result

The archived box-corner screen reported shaft-path hits for 20/20 stacks. Its 80 non-heading obstacle pairs are four self-interferences per stack: the two receiver timbers crossed by that stack and its own head and nut washer rings. An analytic circular cylinder swept along each installed shaft's own axis is clear of all fixed retained obstacles for 20/20 stacks. None of the four individually screened stationary-nut ratchet headings intersects any shaft sweep; each heading is recorded separately so mutually exclusive poses are not combined into a false obstruction. No exact-only obstacle hits were found.

The sweep uses each candidate stack's nominal CAD diameter, 6.35 mm, and travels one under-head length through the original shaft tip. It does not model the separate 6.604 mm generic ordinary 1/4-in shank sensitivity. The analytical shaft sweep remains at least 126.251 mm above the assumed Z=0 floor plane.

These results resolve the old shaft AABB hits as envelope artifacts in this nominal geometric screen. They do not verify bolt-thread behavior, internal socket fit, ratchet engagement or continuous heading access, the larger shank-diameter sensitivity, loose-hardware capture, actual floor conditions, fabrication, or structural performance. The coarse report remains available unchanged for provenance, and all prior access/capture limitations remain.

See the [supplement JSON](wj03-head-withdrawal-exact-shaft.json) for per-stack geometry, fixed-obstacle hits, heading-specific results, and source pins.
