# Implicit bounded contact capture — attempt04

This packet is an additions-only CalculiX 2.23 source/build candidate for a
bounded penalty-contact diagnostic. It preserves attempt03 and incorporates
its source-review findings: the tie count is passed at the declared `ITG *`
level; the single `RUN_END` finalizer is placed after the CLI's complete step
loop; capture storage persists across step calls and is freed/reset at that
job boundary; and generation/trial hooks use the caller's actual `ITG kscale`
type.

The capture lifecycle begins only at the in-loop contact-regeneration call.
The pre-loop seed scan is excluded and its face scan or outcomes cannot be
inferred from this sidecar. Each captured generation requires the complete
pass-1 runtime face/offset census. Source pass 2 is optional per tie: a tie
that enters pass 2 must provide its full face roster and match pass-1
identities, offsets, spans, and live/dead statuses. A tie without pass-2 rows
is unobserved in pass 2, not a zero result. The offline mixed-case control
checks pass 1 for two ties with pass 2 only for the first tie.

The sink caches capture-path availability. When capture is disabled, the
Fortran hooks skip per-face/per-point bookkeeping and calls, and the
post-results spring scan is bypassed. No runtime benchmark was run; the
bounded structural overhead is one cached activity query per generator call,
one begin and iteration-link call per in-loop iteration, one activity query
at the post-results hook, and boolean guards in visited face/candidate loops.
The disabled path performs no per-face/per-point sink calls, hashing,
allocation, or output.

Offline controls compile the standalone sink harness and check source
reachability, exact hook signatures/arguments, additions-only statement
allowlists, optional-pass face accounting, two-step lifecycle, overflow, and
reader rejection cases. The patch was compiled and linked from the pinned
2.23 source archive. The Docker base tag was resolved to its pinned image ID
before building, copied to a one-use locked tag for the `FROM` reference, and
the resolved and built image IDs are recorded in `build/artifacts/`.

No CalculiX executable was run. No coupon or current-joint input was run or
frozen. Source-level nonreplacement and successful compilation do not
establish runtime equivalence, instrumentation behavior in a native case,
mechanics acceptance, or joint acceptance.

The contract references an earlier unmodified exact-touch penalty coupon as a
possible coordinator-only output known-answer check. It is not evidence from
the attempt04 binary. The instrumentation still does not emit point-force
vectors/moments, nodal contact corrections, correction work, a force/work
bound for omitted candidates, or whole-model energy balance. Runtime face-span
conservation does not prove geometric search/clipping completeness, and a
zero net pair resultant cannot prove absence of local bearing.

## Reproduction

From this directory, run the offline controls with:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover -s tests -v
```

The recorded compile/link-only build command is `build/run-build-attempt04.sh`.
It refuses to overwrite image/artifact paths, checks the actual base image ID
against the pinned manifest, builds with networking disabled, and only creates
a stopped container to copy out the binary and build manifest. It never starts
the solver. This build resolved the base tag to
`sha256:31336f517557f5dd5f97d85b1e6e15947fd1c10b44edc1364dbba4c1a5ab6c38`,
produced image
`sha256:fff25d98913701032c2160b3c49f1c1189aeafdd33b09701daafe121f14c9bd9`,
and copied binary SHA-256
`b5a2483cac9d2e208babe8a52c534ec1f3199d34fc8e64accb3005d66507e303`.
The production C hook caller compiled with `-Werror=incompatible-pointer-types`;
the corrected `istep` arguments and `ITG *kscale` calls therefore passed the
compiler's pointer-type check. Offline tests passed 17/17. Exact source, patch,
build, contract, reader, tests, output hashes, and build provenance are listed
in `source-pins.json`.

Attempt01, attempt02, and attempt03 remain preserved. Any later run requires
fresh parent readiness, exact input/include/source/binary/roster rebinding,
serialized execution, and a separate native-output review. This packet does
not select or freeze a current-joint diagnostic.
