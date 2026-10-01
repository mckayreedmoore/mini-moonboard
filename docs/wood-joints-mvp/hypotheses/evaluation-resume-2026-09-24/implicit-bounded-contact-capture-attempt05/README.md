# Implicit bounded contact capture — attempt05 hardening

Attempt05 is an offline hardening package for the additions-only CalculiX 2.23
contact-capture candidate. It preserves the reviewed attempt04 package and
reuses its pinned upstream source archive and build base as inputs. The attempt04
source-pins file SHA-256 is
`7a54d8ad4d85e278b111cc0afadd6abe3e3d77860ca9715ff87591602a2ceea4`; its
patch SHA-256 is
`7aa89782d3026f9d27fbd5f62bb4dbdfb80f11472c861bcc1568f22db3fe474f`.
Attempt05 regenerates a distinct patch from the same source archive after
applying the hardening described below.

The writer stores the pass-1 face roster and compares every observed optional
pass-2 row by tie, ordinal, encoded face, start and end offsets, span, and
live/dead status. A mismatch sets generation completion false. Pass 2 remains
optional per tie; absent rows are unavailable, never a zero result.

The candidate-row limit is 250,000 combined across pass 1 and all observed
pass-2 rows in one generation. It has no additional per-pass allowance. The
independent nintpoint allocation limit is 999,999. The reader checks the
combined candidate total from MAP_SUMMARY records itself, even though the
writer enforces the same limit.

The offline reader requires exactly one `CCXCAP\t1` row at the start, followed
immediately by `RUN_BEGIN`, and rejects any later schema row. It also rejects
missing required record classes, mismatched footer totals, and altered pass-2
identities or offsets. The patch preparer checks additions-only deltas and
applies explicit statement-boundary, trailing-token, assignment-target, and
increment/decrement checks to added C caller code. This is a bounded lexical
policy, not a general C parser; the generated source delta still requires
independent review.

The sink writes beside the requested destination to an exclusive temporary
file. It checks generation and footer flushes and the final close, then uses a
no-overwrite hard link to publish the configured path. Injected failures at a
generation flush, footer flush, or final close leave that path absent. A
structurally invalid capture may still be published with error fields when
writing succeeds, so the offline reader can inspect the failure. The sink does
not call `fsync` and makes no power-loss durability claim. The destination
filesystem must support hard links; a publication failure leaves the configured
path absent.

## Pins and reproduction

`build/context/source.tar.bz2` is pinned to SHA-256
`9c88385c10fb04f5dc6c4e98027a51bebdd8aee3920e05190d6c1dd08357d6e7`.
`build/context/base-image-pin.json` records base image ID
`sha256:31336f517557f5dd5f97d85b1e6e15947fd1c10b44edc1364dbba4c1a5ab6c38`.
The new patch, patch-preparation record, capture sink, source archive, build
base manifest, contract, reader, and tests are hashed in `source-pins.json`.
The attempt05 source pins explicitly record that no patched solver build or
solver run was performed. The inherited upstream Makefile is retained as a
pinned build input only. No attempt05 Docker wrapper, build runner, or modified
CalculiX executable is included.

From this directory, run the offline controls with:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover -s tests -v
```

The suite compiles only standalone C sink harnesses. It does not compile the
patched CalculiX sources, run Docker, invoke a solver binary, run a coupon, or
freeze a current-joint input. A passing suite establishes offline contract and
harness behavior only; it does not establish native runtime equivalence,
contact-search completeness, mechanics acceptance, joint acceptance, or
current-joint applicability.
