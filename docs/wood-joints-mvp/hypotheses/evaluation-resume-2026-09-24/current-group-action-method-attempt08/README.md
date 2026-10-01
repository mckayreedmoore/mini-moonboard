# Current group-action method — attempt08

Attempt08 is an immutable offline source delta from the exact reviewed attempt07 bytes. It addresses the attempt07 correctness finding and the independent test review's path ambiguity observation. Attempts01–07 remain unchanged.

The public sensitivity result now sorts actual changed paths with the same lexical normalization used for the coordinator contract, so valid multi-digit array indices no longer return false `pending`. For list growth or shrinkage, the declared changes include the array `.length` and one indexed path for each added or removed whole item. Object path keys escape backslash, dot, and square brackets with a preceding backslash; the empty key is `\\e`. Literal `a.b` and nested `a`/`b` therefore produce distinct paths.

The package includes the exact attempt07 base files and an additions-only unified patch. Parent replay passed without fuzz and reproduced both maintained files byte-for-byte. The focused attempt08 suite passed: `43 passed in 1.27s`.

This remains a method-only helper. Candidate capacity and criterion disposition remain unset/pending. No geometry, criteria method map, solver, Docker, or current-joint run changed. Independent attempt08 reviews are pending.
