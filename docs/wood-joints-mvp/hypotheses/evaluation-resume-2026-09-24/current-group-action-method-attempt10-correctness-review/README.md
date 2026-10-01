# Attempt10 independent correctness review

No actionable correctness defect was found in the reviewed attempt10 delta.
This conclusion covers the pinned method implementation, focused tests, and
the additional probes described below. It is not a candidate capacity,
criterion disposition, native-method validation, or construction release.

## Reviewed identity

The exact attempt10 terminal manifest SHA-256 is
`b7cf94c61d5b4393f5544c5b59ba7650e231ce4afb3b25743c8bc9f5ec10c7fd`.
All five files named by that manifest match their recorded hashes. The separate
base snapshots match the exact attempt07 maintained hashes:

| File | Attempt07 base SHA-256 | Maintained/replayed attempt10 SHA-256 |
| --- | --- | --- |
| `mini_moonboard/nds_2024_group_action.py` | `f6ba3e0e92ce049c7c22d0407acc5d455609c7ff22ca088ce8ab774c15bf8811` | `121ec9d5399aa3e856b4038232e6d61c628aac42ce2addf8d1ff7e3a0e4c3df9` |
| `tests/test_nds_2024_group_action.py` | `dc03a74055f53c001d2ad17d36af47045302e3a85c4fcc0a7d054fdd07079d25` | `741ef514d6a7ea6a88c24f95a53241d126b61e4cd8af6c13d7288268b18adef9` |

Attempt07's referenced patch and terminal manifest match the attempt10 pins;
the latter names these exact attempt07 maintained hashes. Attempt09's
referenced terminal manifest also matches its pin. This review independently
replayed attempt10 from its attempt07 base, without rerunning historical
attempts or reading older review reports.

The criteria method map matches
`2d9083d4286e328553183e0bb993cfb913985fbe4960717bfe0bb4ef416d32e7`.
All 36 legacy criteria and eleven additional obligations remain pending.
Full input hashes, commands, and observed output are in
[`verification.json`](verification.json).

## Replay and focused tests

The attempt10 base directory was copied to a new temporary tree before
applying the patch with `patch --batch --forward --fuzz=0 -p1`. Both files
patched without fuzz or offset, and both replayed files match the maintained
files byte for byte. The immutable base files retained their original hashes.

The copied test file ran against the replayed module using the repository
virtual environment, with bytecode and pytest cache writes disabled. Plugin
autoload was disabled to isolate the focused suite. The result was
`51 passed in 0.08s`. The probe also checked the imported module's absolute
path to confirm it came from the isolated replay.

## Correctness checks

The comparison at maintained module lines 730–740 sorts and deduplicates both
actual and declared paths. This consistently uses lexical string order,
including indexes 10 and above, while retaining exact set equality.

The list branch at lines 568–586 visits every common index, records each
added or removed whole tail item, and records the list length change. Growth,
shrinkage, empty-list transitions, and middle insertions/removals were checked.
Middle changes are positional: shifted common items are differences and the
excess tail item is an addition or removal.

The object-key encoding at lines 548–560 distinguishes punctuation from path
separators, literal backslashes from escape markers, empty keys from literal
`\e`, and whitespace keys from literal `\uXXXX` text. Simultaneous literal
and nested paths remained distinct. Nested `scenario_id` and `source_bindings`
changes under an empty root key were retained; the two deliberate root-only
exclusions did not spread into nested objects.

Additional full-helper probes accepted ten complete contracts and rejected
49 contracts with one changed location omitted. They covered reversed
contract ordering, multi-digit indexes, escaped keys, whole-item list paths,
boolean/integer and integer/float changes, and signed zero. Four further
probes rejected tuple values, non-string keys, NaN, and infinity. A bounded
generated corpus of 1,464 keys, using punctuation, backslash, ordinary
characters, and whitespace, had distinct nonblank encodings. This corpus is
a regression probe, not an exhaustive proof for all Unicode strings.

The strict input digests, contract content digest, independent binding,
coordinator review status, composite classification, scenario identities,
same load case, supported factor scope, and exact changed-path checks remain
in place. Successful method results still report `capacity: null` and
`criterion_disposition: pending`; failed contracts remain pending.

The additional probes and their observations are preserved in
[`adversarial-probe.py`](adversarial-probe.py) and
[`adversarial-probe-output.json`](adversarial-probe-output.json).

## Scope and terminal state

The patch changes only the method's sensitivity-path logic/docstring and the
focused test file. The criteria map and every pinned review input were
rehashed at completion and remained unchanged. No source implementation,
immutable attempt evidence, geometry, criterion disposition, or solver input
was edited. No solver, Docker, or native execution was invoked. Only this
review directory and isolated temporary replay/probe files were created.

The source review does not establish the authority of caller-supplied
manifests or validate candidate demand/capacity. All structural criteria
remain pending. [`terminal-hashes.json`](terminal-hashes.json) binds this
review's report and supporting files.
