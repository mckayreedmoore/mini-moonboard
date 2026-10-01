# Independent review — current taper bore clearance preflight attempt02

**Disposition: PASS for the packet's bounded geometry-only purpose. No defects found in the reported cylinder mapping or taper-envelope arithmetic.** This review does not provide a structural disposition.

I independently rechecked the attempt02 source-pin set, including the exact attempt01 report, producer, test and packet bytes, and revalidated all 216 upstream taper-preflight pins. All hashes match. The attempt02 packet `SHA256SUMS` verifies, and the producer's read-only `--check` replay reproduces report SHA-256 `37c79990fb257797723152f07c5c6a855bb9a5ffbb18e5b29c6531beca6c0218` with eight mapped bores and the criterion pending. The focused suite passes (8 tests); Ruff passes for the producer and tests.

My separate OCP/CadQuery read of the two pinned leg STEP solids finds four analytic cylinder faces per leg. I mapped each face to exactly one of the four retained frame-bolt axes naming that leg, using parallel axis direction, perpendicular centerline distance, and the manifest's member-pair association. The mapping is one-to-one across all eight faces. I then projected each bounded cylindrical face's full circular envelope onto the pinned grain direction and compared it with the pinned taper interval. All eight producer intervals and gaps reproduce within 1e-9 mm; the minimum gap is 50.712771543481296 mm. The full-circle envelope is conservative for angularly trimmed faces. The independent values and row-by-row comparison are in `independent-audit.json`; `independent_audit.py` reproduces them without importing the producer's calculation functions.

The tolerance values (1e-5 mm for geometry and 1e-10 for axis direction) match the pinned taper preflight's source tolerances. They are exact-model comparison tolerances, not physical machining or installation tolerances. The reported gaps are much larger than the geometry tolerance. Source hash drift, incomplete/duplicate inventory, missing or ambiguous cylinder mapping, invalid finite values, receiver/interval mismatch, or unavailable CAD runtime cannot produce a clear disposition: they raise or leave the screen unresolved. The focused tests exercise representative fail-closed cases.

The bore claim is limited to source-pinned CAD: eight modeled cylindrical faces in the legs plus the 92 candidate structural bolt-axis receiver memberships. The 12 retained frame-bolt axes are inventoried; four per leg map to those faces, and none of the 92 candidate structural bolt axes lists either leg as a receiver. I separately checked the manifest's 66 panel/kicker screw axes, which are the distinct Hillman 42605 policy: none names either leg in its `receiver_member` field. Those screws are not candidate structural bolt axes, and this review does not claim that their physical holes, screw occupancy, delivered hardware, or installation were inspected. This separate inventory check does not change the packet's bounded result; keeping the Hillman policy distinct avoids implying that it was included in the 92-axis structural-bolt audit.

The packet correctly leaves `taper_taper_region_unbored_torsion_applicable` **pending**: the adopted criterion requires a fresh current case. This screen establishes neither actual cuts/holes nor native/CAD identity, mesh equivalence, torsional resistance, physical fit, failure-mode qualification, candidate acceptance, fabrication release, or climbing release. All three release flags remain false.

## Verification record

- Attempt02 fixed source pins: all match, including attempt01 preservation pins.
- Upstream taper source pins: 216/216 match.
- Attempt02 packet checksum sidecar: all files match.
- Producer replay: `.venv/bin/python -B scripts/build_current_taper_bore_clearance_preflight_attempt02.py --check` passed; 8 bores, no candidate structural leg receivers, criterion pending, release false.
- Focused tests: `8 passed`.
- Ruff: producer and focused tests pass; this review's independent auditor also passes Ruff.
- Independent geometry reconstruction: 8/8 cylinders uniquely mapped; all reported envelope intervals and clearances agree within 1e-9 mm; zero tolerance-expanded overlaps.
