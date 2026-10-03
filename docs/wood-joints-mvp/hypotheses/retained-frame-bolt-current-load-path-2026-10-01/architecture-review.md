# Architecture review

**Result: pass for the stated demand-only scope.** The packet binds the twelve
retained frame-bolt arrangements to the current finished geometry and the
frozen conditional response. Its 92 candidate-bolt axes remain a separate
group. The report covers all 21 states, and each state carries the complete
eight-body boundary: 568 physical interfaces and 720 scalar channels. This is
not a retained-bolts-only subset.

The producer authenticates the feature register, finished STEP files, model,
deck, DAT, response, all-body audit, terminal records, physical projection,
source geometry and imported helper by SHA-256. It checks each retained axis's
two receiver memberships, finite bore intervals, owners, scalar source rows,
projection rows, force laws and current points before joining forces. Missing,
duplicate, changed or contradictory source records fail closed. Its boundary
is enumerated from every raw model interface touching the eight bodies; the
response join and per-body balances include those ports and the physical nodal
loads. The report's counts and separate retained/candidate axis census agree
with that construction.

The producer imports the pinned corner exporter, but calls its vector and
moment arithmetic, floor-reaction reconstruction, response-owner validation
and member-balance helpers only. It does not call that exporter's old geometry
or resistance paths, and the import has no native-solver or CAD execution path.
Current axis points and seat points come from the authenticated feature
register and current response owners. Body moments use the all-body audit
references; descriptor midpoints are reported separately. The exported
transported actions are not bolt internal bending, and no origin-moment
acceptance gate is introduced.

One replay defect was found and fixed during review. The pinned adapter builds
its interface map from a set, so its output insertion order varied across
process hash seeds and changed floating-point summation order by immaterial
roundoff. The producer now sorts the reconstructed interface map before
balance sums and serialization in [produce.py](produce.py#L398). Two fresh
`--check` replays under different hash seeds are byte-identical and match the
regenerated canonical report at
`/tmp/mini-moonboard-retained-frame-bolt-current-load-path-2026-10-01.json`.

The independent [raw-token oracle](raw_oracle.py) was also reviewed and replayed
against that report. It uses only the standard library, parses force tokens and
their print-rounding radii directly from the frozen DAT files, and imports
neither the producer nor a response parser. Its bounded map recovers the two
SPRING2 components and one SPRINGA tie for each retained axis, then checks the
report's signed scalar and vector actions, interface owners, combined endpoint
wrenches, moment transport and audit datums. It covers all 21 states, 756 raw
channel states, 504 combined endpoint wrenches and 168 datum references while
keeping the 92 candidate axes separate.

The oracle initially lacked an independent pin on the freeze that selects its
source files. That gap is fixed: it now requires freeze SHA-256
`d4ba1c78eb358d25e32819201e9c59e05d425a06d9e4e5cca3dc09d7139ffd73` and checks
the report's `input_pins` entries for both that freeze and the projection
contract against their pinned digests. It then verifies the model, DAT and
all-body audit bytes against the authenticated freeze. The oracle replay passed
with report SHA-256
`f068cd5afc93c2b7027624b1fbec94ccb419f664833d920d2959f79bed661cc1`; its
result records hashes for the report and each source input.

The remaining limits are deliberate scope boundaries, not architecture
defects: only A1-rear, A12-rear and K12-rear at seven factors are joined; the
packet establishes no resistance, capacity, internal bolt bending, local
stress, hardware compatibility, inspected physical condition, floor
qualification, joint acceptance or fabrication release. The independent
oracle is bounded to the retained 12-axis force and wrench reconciliation; it
does not extend the result to the 92 candidate axes or establish acceptance.
Final validation receipts remain tracked by [validation.md](validation.md).
