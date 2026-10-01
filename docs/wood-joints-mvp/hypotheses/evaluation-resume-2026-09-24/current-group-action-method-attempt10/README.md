# Current group-action method — attempt10

Attempt10 is an immutable offline source delta from the exact reviewed attempt07 bytes. It preserves attempt08's detected packaging error and attempt09's corrected replay chain, then adds focused coverage for the remaining path-encoding and list-removal edges.

Sensitivity paths are sorted consistently with coordinator contracts, including rows with multi-digit indexes. List growth or shrinkage is represented by the list `.length` and an indexed path for each added or removed whole item. Object keys escape backslash, dot, and square brackets by prefixing each reserved character with a backslash. An empty object key is encoded as one backslash followed by `e`. A nonempty all-whitespace key is encoded as one `\uXXXX` token per code point, so it can be written in a nonblank contract string. Tests distinguish literal punctuation keys from nested/object and array paths and exercise growth and shrinkage contracts.

The attempt10 base files are exact attempt07 maintained bytes (`f6ba3e…` module; `dc03a7…` tests) and remain unchanged after replay. Parent no-fuzz replay in a separate temporary tree reproduces maintained attempt10 bytes exactly. The isolated focused suite passed: `51 passed in 0.08s`.

This remains method-only. Candidate capacity and criterion disposition remain unset/pending. No geometry, criteria method map, solver, Docker, or current-joint run changed. Fresh independent attempt10 reviews are pending.
