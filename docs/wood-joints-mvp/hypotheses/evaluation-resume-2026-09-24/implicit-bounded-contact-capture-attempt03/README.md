# Implicit bounded contact capture — attempt03

This packet compiles an additions-only CalculiX 2.23 sidecar capture for a
bounded penalty-contact diagnostic. It fixes two lifecycle defects identified
in the earlier source/build attempts: the in-loop generation hook now passes
`ntie` at the declared `ITG *` level, and one finalizer runs in the CLI `main`
after the complete step loop and native output close. The sink remains alive
between steps, emits one job footer, then frees and resets its pointer/length
pairs. A pending-generation guard makes a later end-hook call outside a begun
capture sweep a no-op.

The capture observes only the in-loop contact regeneration call. The earlier
pre-loop seed scan is deliberately excluded and cannot be inferred from this
sidecar. Face-span conservation covers the exact runtime face slots presented
by the solver; it does not prove that geometric search or clipping found every
possible point. The finite adjacent-sweep key is not a geometric identity
proof, and `igauss` is sweep-local rather than a persistent point identity.

The stream can account for candidate classification, generated spring counts,
observed trial force and stored energy, and accepted iteration links under the
contract in `capture-contract.json`. Missing, unmapped, excluded, or unjoined
values remain unavailable; they are never treated as zero. The capture does
not emit point-force vectors or moments, nodal correction vectors, contact
correction work, force/work bounds for omitted candidates, or whole-model
energy balance. A zero net pair resultant cannot prove absence of local
bearing. The packet does not select or freeze a current-joint model and does
not establish a joint capacity or structural acceptance.

## Verification state

The dedicated binary compiled successfully from the pinned 2.23 source archive
and patch. The build used the recorded Docker image and compile/link command;
the build container was created only to copy out the binary and manifest. The
solver executable was never invoked, and no coupon or current-joint case was
run. The local C sink and Python reader/source-policy suite passes 15 tests;
the exact command and captured output digest are recorded in
`offline-test-results.json` and `offline-test-output.txt`.

`capture-contract.json` references a prior unmodified 2.23 exact-touch coupon
and standard output as a future coordinator-only force/energy known-answer
check. Those references are not results from this patched binary and do not
qualify the capture implementation. Any future capture use needs independent
parent review, exact input/include/source/binary/roster rebinding, and a
separately authorized serialized native qualification. Attempt01 and attempt02
remain preserved unchanged.

## Reproduction and pins

From this directory, rerun only the offline controls with:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover -s tests -v
```

The one-shot compile-only build script is `build/run-build-attempt03.sh`; it
refuses to overwrite its recorded image tag or artifact directory. Source,
patch, build context, output binary, image ID, and test files are bound in
`source-pins.json`. The executable SHA-256 is
`6da2b6ccccc69bf824bec9fdcc1ba73d4e2f54cfe491978e8933800d6a730233`; the
recorded image ID is
`sha256:9a9fe7cfb180c3cfcd8c4af7b652f05670b3f458bd0b1cfae5ca0ba889bee1df`.
