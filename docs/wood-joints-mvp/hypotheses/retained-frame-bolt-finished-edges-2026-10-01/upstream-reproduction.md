# Frozen upstream reproduction

This packet consumes three frozen outputs rather than rerunning native
mechanics. The upstream producers replay authenticated saved geometry,
projection and native-result bytes. They neither launch CAD nor native solves.
The root agent reproduced all three into separate temporary files and matched
the accepted hashes below before this handoff.

| Required artifact in `/tmp` | SHA-256 |
| --- | --- |
| `mini-moonboard-retained-frame-bolt-current-load-path-2026-10-01.json` | `f068cd5afc93c2b7027624b1fbec94ccb419f664833d920d2959f79bed661cc1` |
| Same load prefix, `-raw-oracle.json` | `c6d43017d67f864dfc25e6a77832a542a97257a1da23f4ca3a12e82d6a829ea9` |
| `mini-moonboard-retained-frame-bolt-current-resistance-basis-2026-10-01.json` | `c3250f067c4590ee43f7ec7a5765d056d87e6ff5adb42837ed27710d9b4d4eb1` |

From the repository root, when these canonical artifacts are absent, reproduce
them in this order using the pinned upstream code:

```sh
.venv/bin/python docs/wood-joints-mvp/hypotheses/retained-frame-bolt-current-load-path-2026-10-01/produce.py --check > /tmp/mini-moonboard-retained-frame-bolt-current-load-path-2026-10-01.json
.venv/bin/python docs/wood-joints-mvp/hypotheses/retained-frame-bolt-current-load-path-2026-10-01/raw_oracle.py --report /tmp/mini-moonboard-retained-frame-bolt-current-load-path-2026-10-01.json > /tmp/mini-moonboard-retained-frame-bolt-current-load-path-2026-10-01-raw-oracle.json
.venv/bin/python docs/wood-joints-mvp/hypotheses/retained-frame-bolt-current-resistance-basis-2026-10-01/produce.py --load-report /tmp/mini-moonboard-retained-frame-bolt-current-load-path-2026-10-01.json --raw-receipt /tmp/mini-moonboard-retained-frame-bolt-current-load-path-2026-10-01-raw-oracle.json --output /tmp/mini-moonboard-retained-frame-bolt-current-resistance-basis-2026-10-01.json
```

Do not overwrite an existing accepted artifact to recover from a failed
replay. Preserve its bytes and investigate the missing or changed source. The
finished-edge producer authenticates all three hashes before consuming them.
The load oracle receipt records the canonical load-report path, so keeping that
path is necessary for byte-identical receipt reproduction.

Upstream code pins are `af0a9569da228a8858f23107c16c7c8b3d9e0dbb50769733b5a399743eea6e24`
for the load producer, `9d04a698227d42207533e23b33afa08b7031518d8c80499251cdf4d4e791e758`
for its raw oracle, and `24b3cb82ed6a785ab5dc0cf910f22a0cce915438f8d4b04d527d82a245b1205b`
for the resistance producer. They are included in this packet's authenticated
source chains. Their original validation records remain preserved in the
[load packet](../retained-frame-bolt-current-load-path-2026-10-01/validation.md)
and [resistance packet](../retained-frame-bolt-current-resistance-basis-2026-10-01/validation.md).
