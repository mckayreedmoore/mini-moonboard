# Luna coordinator consistency audit — attempt05

Audit date: 2026-09-28. This read-only audit binds the live queue, status, handoff, and artifact-manifest bytes below. It covers the current T08 attempt02 and T09 attempt03 coordinator updates. It does not change those records, source-snapshot authority, criteria, or candidate evidence.

## Verdict

**PASS, with one explicitly permitted frozen-source pin drift.** All 286 artifact-manifest entries exist and match their SHA-256 values. The queue/status/handoff bindings are current; all 323 repository-relative queue file references and all checked local Markdown links resolve. The 12 immutable source-snapshot pins match. T08 and T09 remain active, all 47 criteria remain pending, and engineering/release completion is false.

T08 attempt02 closes only source/count/arithmetic and deterministic planning checks. It does not select or qualify products/materials, establish post-rip grade or a purchase quantity, or provide a candidate cost bound. T09 attempt03 passes conditional orientation coverage only; it does not provide actual material assignment, a full-frame mesh, solver maps, mechanics, readiness, or release. No T08/T09 state or evidence advances an engineering criterion.

The live T08 cost packet retains its queue hash from its freeze (`e624e043…57a0a35c`); the current mutable coordinator queue hashes to `7fe3f33b…ed2f06ca0`. Its follow-up record explicitly permits only that queue path to drift and computes the live queue digest dynamically. The other 29 source pins match. This is expected coordinator evolution, not a new packet defect.

## Bound coordinator snapshot

- `docs/wood-joints-mvp/luna-max-task-queue.json` — SHA-256 `7fe3f33b98a9dc2369a91c345848a67e8c1aee18b55496181a88d26ed2f06ca0`.
- `docs/wood-joints-mvp/luna-max-status-2026-09-28.md` — SHA-256 `06a70b505232723e05de3649af2e3b2f89b07b14d5dd7bf7ab86bfb406171fef`.
- `docs/wood-joints-mvp/luna-max-completion-handoff.md` — SHA-256 `667673720ad417f36da50742aa50862c9e8d14fabfa4d4134c8d49d8f1c21f33`.
- `docs/wood-joints-mvp/artifact-manifest.json` — SHA-256 `1afcb9be49b1d92feb45edc90956a10c77222d5f8a146534d217f2e517a1686c`.

Queue and manifest pass duplicate-key-rejecting JSON parsing and declare their expected schema identifiers. Twelve T08/T09 packet JSON records checked for this audit also parse without duplicate keys. The manifest lists 286 files: 286 exist and zero hashes mismatch. It binds the current queue, status, and handoff hashes above. The queue's live status path resolves, and `plan_review.handoff_document_sha256` equals the live handoff hash. The status has 33 local links and the handoff has 68; all resolve. The queue file-reference scan found 323 repository-relative paths and no missing paths. All 28 T08 and 29 T09 task terminal-artifact paths exist.

Candidate/revision remain `compact-floor-flush-wood-joints-development` / `led-clearance-2x6-runner-seated-blocks-v1`. All 12 entries in `source_snapshot_sha256` exist and match exactly. The 47 criterion rows have 47 unique IDs and all 47 handoff statuses are `pending`. Queue `release=false`, queue `engineering_mvp_complete=false`, checkpoint `engineering_mvp_complete=false`, and manifest `release=false`. T08 and T09 task rows are both `active`; their gates remain open.

The separate current-map method fixture still records scoped `current_map_readiness=true` and `current_map_native_execution=true`. These fields do not mean the current joint or full-frame candidate is ready. T08/T09 attempt records report `native_execution=false`; T09 attempt03 sets full-frame material readiness, inputs, launch, and native-solve readiness false, with acceptance, native execution, and all release flags false. T02/T03 runtime/readiness gates also remain closed in the live queue and status.

## T08 attempt02 bindings and limits

T08 remains active, with phase `attempt02_partial_closeout_independently_reviewed;followup_verifier_pass;product_fit_stock_yield_and_cost_gates_open`. Its next action continues exact compatible product/material identity, matched-stack requirements, source-backed prices, and defensible order quantities; candidate totals and ranges remain null.

The public-price/count closeout pins 30 unique sources. Its frozen `source-pins.json` hash is `9599644387190295190ddbb5ab2661ee6c171d80fbf111e42b8a03c8942ff22e`; its `SHA256SUMS` file hash is `baaac3c26624c92ff96e391cbc914366321c37081186a3d212ee424754da09fd`. The packet checksum verifies all seven listed payload files. The bound independent review is `SUPPORTED_PARTIAL_FAIL_CLOSED`: its README, review record, and checksums hash to `6b4cb0fe534f6abb5889aa052890fe0b0a7b0e1d666aa5dccaf4c1002f31b3af`, `814588b80d9524291cbc0c717b3b872e7b88e81710dc7d0d5267d7a4a2c67610`, and `44ac19c4996c39a318bdb9c8b119c6d31125b088ccd52f395f077e90ea0798b1`. The follow-up README, record, and checksums hash to `8cdb6197e8d003ae70b0e6a1c7b461d7940643c5c7315b608144299899978e96`, `a48639b7ca923ad01f20bc2359cf5a3467f3920cd5f3f8f42a81b58212da395c`, and `b7dc9ecb2c9d2e32e84dd6cf6dc09d3ceb702615448c4728797c53c6038080ac`; both review checksum sets pass. It preserves the partial verdict and only permits post-freeze drift in the mutable task-queue pin.

The queue reconciles 92 candidate bolt axes, 12 retained starting frame-bolt axes, 66 Hillman 42605 axes (58 unchanged, eight previously moved), and 144 removed SDS25112 references. Eight public bolt-lead pages have displayed prices, but their unlike lengths and tiers are not candidate bounds. The verification record keeps candidate selection false, candidate total/range null, Hillman receipt cost null, material-cost bounds null, received identity/receipt unasserted, and product-specific weight/fit acceptance unclaimed.

The appended cut-yield attempt02 subtask is `parent_and_independent_review_pass_planning_arithmetic_only;material_grade_purchase_and_cost_gates_open`. Its eight queue-pinned artifact hashes all match:

| Artifact | SHA-256 |
| --- | --- |
| Producer `scripts/build_current_timber_cut_yield_scenario_attempt02.py` | `027479a0f082c036da5bba603defea348c4d97ca4be7f76626177a03e077bc7d` |
| Test file `tests/test_current_timber_cut_yield_scenario_attempt02.py` | `5ddf1e03cd7abbd095aec6368e0026e9bf87bd86f80a2fccbea199e408806866` |
| Attempt02 `README.md` | `7491d8fe3531190d92976e9a02ea5d063debb81bd6f5d54b20640fdc6a3c69aa` |
| Attempt02 `source-pins.json` | `e24b70e2c4de79918b7b654a3f789d820b9cf63bbdcc4ae77f41350f6b70e46e` |
| Stored scenarios JSON | `df1f4e2df03f1f65870d71f4a63708fbc06a4dd0a5ca9f9f527ff30a63249c30` |
| `verification.json` | `0756de1f74158f9d844f4b71fe1acce40ecf91b6994368d9e2f11fe4909061e8` |
| Independent review `REVIEW.md` | `f645ab7fe4f2ad2cff2707db66939280aebb3e38e53a5472bd181bd283da3361` |
| Independent review `SHA256SUMS` | `0d939ea0cc0692e7e505247f6c27a633d889b828863f3aa0bcd6cde87d637fc3` |

All 14 unique yield-source pins match. The stored verification reports 30 deterministic length-arithmetic scenarios, 24 blanks, `source_pins_status=PASS`, and `physical_or_purchase_claims=false`; the independent review reports 30/30 recalculation agreement and 15 focused tests. The scenario record remains planning arithmetic only: the four post-rip grade dispositions, accepted stock, physical cutting, purchase quantity, and costs remain unresolved. Test and reviewer results are recorded from the packet; this audit did not rerun them.

## T09 attempt03 bindings and limits

T09 remains active. The attempt03 subtask is `parent_and_independent_review_pass_conditional_orientation_only;full_frame_readiness_open`, with `native_execution=false`. All eight queue-pinned artifact hashes match:

| Artifact | SHA-256 |
| --- | --- |
| Producer `scripts/wood_joint_current_frame_material_frame_coverage_attempt03.py` | `4d857850d4199f59256763dff15065ea31bb7ec115c840c46c0692a35b2fa91c` |
| Test file `tests/test_wood_joint_current_frame_material_frame_coverage_attempt03.py` | `0c80ed67b0535638d8d17bc272faf1d0415b8ad48c226b4cc26fe6ca88a5b03e` |
| Attempt03 `README.md` | `880d99bd125da08bab5f8d177877fd5be4ec825593ef28a42f3ea164b0cb81ce` |
| Attempt03 `coverage.json` | `530871fd917e6566e508f69b75282674781b11eae29aaf37afb0675cf906bc3d` |
| Attempt03 `source-pins.json` | `4ed640f0c0051ce29c20af2818ec173e62afded072c7d9a61e9cc647c4fc9ba3` |
| Attempt03 `SHA256SUMS` | `59913f8e69a8a4a264dfb68b5a576a13ab55d6a8c194c818792e03c77adea881` |
| Independent review `report.md` | `11b9f9b7e029af12bc1d85a3197a70197646d49aa483089fd4c6dbfcfcf1de9e` |
| Independent review `SHA256SUMS` | `37f4564f4d2acad92f23d97a64562fa193f71d7936603fecda21dda09e55cd09` |

The packet source-pins file authenticates 68 unique lineage files; all match, along with its attempt01 and attempt02 review records and seven attempt02/review artifacts. The independent report confirms all 48 block scenarios across 24 blocks, including the complementary radial/tangential labels and signed `T = L × R` basis. The exact-body inventory is 50 entries: 20 frame timbers, 24 candidate blocks, and six unresolved plywood panels.

The record describes only conditional source geometry/material-frame orientation, not observed delivered stock. Timber grade/species properties, product assignments, all six panel layups/axes/properties, and all solver body/element/node/DOF maps remain null. Readiness, acceptance, native execution, and release flags in `coverage.json` are all false. Its boundary expressly excludes a mesh, mechanics model, joint response, load transfer, criterion disposition, fabrication readiness, and candidate acceptance. The independent review records six attempt03-focused tests; this audit did not rerun tests or the producer verifier.

## Historical audit and documentation alignment

Attempt04 remains valid as history for the exact earlier snapshot it names. Its report SHA-256 is `02fd69281bd6226a9f8fc8f3dc228e0a83eb9f5fe7d3dcc3ecb0cc30c0b6269d`, and its sibling `SHA256SUMS` verifies it. It bound queue `a50122a85d9a1ff5db558d658dce8d052580e858293e9abeba3fe08834bba7af` and manifest `93b2e9f790e52b5825c3a73ff3f491373a03cd05337abb7b528e26e017409411`; it is historical evidence, not the audit of this newer queue/status/manifest.

The live status and queue pending note describe the new T08/T09 packets and preserve their planning-only/conditional-orientation limits. The handoff digest is unchanged from attempt04 and its summary does not enumerate the newly added cut-yield and orientation-coverage attempts. Its stated T08 cost/yield, T09 mesh/panel/readiness, and physical-operation gates remain open and are compatible with the live status; no conflicting acceptance claim was found. The handoff remains an execution plan, while the queue and live status carry current scheduling state.

`plan_review.status` remains `checkpoint_update_pending_independent_consistency_review`. After this result is reported, it can be closed as a coordinator-consistency checkpoint by binding this report and the current queue/manifest digests. That metadata update does not require changing the 12 `source_snapshot_sha256` entries.

## Method and limits

I strictly parsed the queue, manifest, and 12 relevant T08/T09 packet JSON files with duplicate-key rejection; recomputed every manifest digest and all 12 source-snapshot pins; checked queue/status/handoff bindings and Markdown links; resolved queue references and T08/T09 terminal paths; validated the exact current subtask hash maps, packet checksum files, source-pin lineages, state fields, and claim boundaries; and checked the prior attempt04 report checksum. I ran no project tests, producer verifier, solver, Docker command, native mechanics run, or engineering disposition. Test counts above are frozen packet/review results, not audit executions. This report is outside the audited manifest; its SHA-256 is supplied with the audit result.
