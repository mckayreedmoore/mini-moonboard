# Coarse moving-control evidence

The native moving solve completed 200 increments through 2e−5 s in about
1110 seconds, with native exit 0 and successful owned-container cleanup.
The first bounded audit then stopped at its pressure/penetration check,
**before the full momentum/energy balance was evaluated**. No moving-contact,
refinement, joint-capacity or structural qualification has been established.

Raw native output is retained in [control.dat.gz](control.dat.gz),
[control.frd.gz](control.frd.gz) and [native-other.tar.gz](native-other.tar.gz),
with identities recorded in [native-output.json](native-output.json).

## First audit and pressure diagnosis

[first-audit.tar.gz](first-audit.tar.gz) preserves the complete first audit
runtime, supervisor snapshot, command, traceback, exit and owned-CID cleanup,
plus the read-only diagnostic script/report. The audit process exited 1 after
35.999 seconds; cleanup exited 0 and the container was not OOM-killed. No audit
report or numerical pass was produced. Its frozen limits were 900 / 920 seconds,
8 GiB memory/memory-plus-swap and two CPUs.

The read-only contact scan identified two failed rows among 582,445 aligned
rows across all 200 states:

| Time | Interface | Positive gap (mm) | Negative pressure (N/mm²) |
| --- | --- | --- | --- |
| 1.07e−5 s | Washer bore | 1.552056e−8 | −0.001552056 |
| 1.61e−5 s | Washer head | 4.199942e−9 | −0.0004199942 |

Both follow the signed native relation `pressure = −100000 × clearance` and
fail the audit's nonnegative, clamped-pressure requirement. Both print CELS=0;
that observation is **not** validated by the source spring-energy formula.

CalculiX 2.21 suppresses positive-gap springs during contact generation
(`gencontelem_f2f.f:551–560`), but generation precedes the final displacement
update (`nonlingeo.c:2291–2311,3140`). Final output recomputes existing springs
without another generation pass (`:3677–3735`), using a signed linear law
(`springforc_f2f.f:157–164,191,253`). This explains how conditional negative
pressure can reach output; it does not establish acceptable unilateral contact.
CDIS/CSTR use the same contact-element traversal and state. Source identities
and the detailed chain are recorded in `references.json` inside the archive.
Diagnostic runtime was session-observed, not archived; the original failed
audit and its gates remain unchanged.

A subsequent [source-level energy-index investigation](../../../docs/contact-energy-output-investigation.md)
found that spring energy is stored using a potential-integration-point index
but printed using the compact contact-element index. Sparse activation can
therefore produce missing or misassigned CELS values; the two individual rows'
hidden indices are not exposed in DAT. Printed contact energy remains unqualified.

Next: a separately labeled **fail-only momentum/kinetic-energy diagnostic**,
and a tiny sparse-contact output check before relying on contact energy or
preregistering any acceptance change. No automatic refinement, solver rerun or
frame alteration follows from this result.

First-audit archive SHA256:
`3c1ca9a3a281a928cf2194e0e15d9102ba657b8f1af693e4f62e745f2b8b4e66`
(10,772 bytes; 13 members). Portable tests verify the failed runtime and recover
the two rows by streaming the retained compressed DAT, without a solver or
full-balance evaluation:

```sh
uv run pytest tests/test_coarse_moving_audit_publication.py -q
```

## Selected preparation

[preparation.tar.gz](preparation.tar.gz) contains:

- `prepared/`: `moving-event-tnev6k3a`, including the pinned passed posed-quiet
  archive, protocol, source snapshots and the coarse moving deck.
- `mass/`: `mass-cache-c4qwd4l5`, containing the separate native four-point and
  physical Gauss8 operators bound to that exact context and deck.
- `solve/`: only the freeze and frozen inputs of `moving-9gsvcbgg`. No active
  results or launch record are included.
- `members.json` and `references.json`: exact member hashes, selected paths,
  source commit `bd17eac78586d51b8d74945b12f7395671930198`, and prerequisite identity.

Archive SHA256: `053d6c06995cb76c666ec8eae85178be299747db96cadd220cabc8355bb5c9d1`
(58,838,330 bytes; 68 members).

The selected event has 200 DIRECT increments of 1e−7 s through 2e−5 s. Only
the washer initially moves, at `(-100,100,0)` mm/s; the core is initially
stationary and both bodies remain free. The frozen solver caps are 1800 seconds
inside / 1820 seconds outside, with 4 GiB memory and two CPUs. These are numerical
experiment settings, not structural design loads or acceptance.

Portable replay checks the archive inventory, preparation/source/cache/launch
input identity, coarse settings and full cached operators. It does not rerun
CAD, Gmsh, the prerequisite quiet proof, a solver or a moving audit:

```sh
uv run pytest tests/test_coarse_moving_publication.py -q
```

See the [moving protocol](../../../docs/moving-hardware-control.md) and
[passed posed quiet evidence](../posed_hardware_control/README.md). Earlier
evidence archives are unchanged.
