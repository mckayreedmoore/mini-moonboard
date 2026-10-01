# Current group-action method — attempt09

Attempt09 is an immutable offline source delta from the exact reviewed attempt07 bytes. It fixes the attempt07 changed-path defects and the attempt08 package replay mistake. Attempt08 is preserved as evidence of the packaging error; its included base contained the patched bytes, so it could not be replayed.

The public sensitivity result sorts actual changed paths with the same lexical normalization used for the coordinator contract, so valid multi-digit array indices no longer return false `pending`. For list growth or shrinkage, changed paths include the array `.length` and one indexed path for each added or removed whole item. An indexed item path identifies the entire item subtree. Object path keys escape backslash, dot, and square brackets with a preceding backslash; the empty object key is encoded as a backslash followed by `e`. Literal `a.b` and nested `a`/`b` therefore produce distinct paths.

The `base/` files are the exact attempt07 maintained bytes (`f6ba3e…` for the module and `dc03a7…` for the tests); the attempt09 patch applies to a separate replay copy, so the packaged base remains unchanged. Parent no-fuzz replay reproduced the maintained attempt09 files byte-for-byte. The isolated focused suite passed: `43 passed in 0.08s`.

This remains method-only. Candidate capacity and criterion disposition remain unset/pending. No geometry, criteria method map, solver, Docker, or current-joint run changed. Fresh independent attempt09 reviews are pending.
