# Independent correctness review — ordinary-joint case classification attempt04

Date: 2026-09-28  
Result: **CLASSIFICATION SUPPORTED; REMAINING GATES AND CLAIM LIMITS CONSISTENT**

## Scope and integrity

Reviewed `ordinary-joint-actuation-map-binding-attempt04-case-classification-2026-09-28/` for packet/source integrity and whether `CLOSED_COMPONENT_CHARACTERIZATION_ONLY` follows from the exact six-case contract, current T09/T10 state, attempt09 history, and T02/T03 coupon gates. The packet `SHA256SUMS` passes from its directory. All 20 files in `SOURCE-SHA256SUMS` pass from the repository root. No packet or coordinator file was changed. This review does not accept mechanics.

## Findings

The classification is supported and bounded:

- The pinned `current-load-cases.json` contains six applied cases (`a12-rear`, `a12-forward`, `a12-left`, `k12-right`, `k12-rear`, `a1-rear`). Its limits state that these are applied forces and equivalent global wrenches only; the contract computes no frame reactions, connection demands, joint/contact laws, load sharing, or capacity. The six cases do not contain simultaneous local rail/principal port histories or a physical time basis.
- The current full-frame manifest independently reports `inputs_ready=false`, `current_full_frame_demands_available=false`, `native_solve_executed=false`, and no complete mechanical contact/attachment model. Its README says no full-frame FE model, reactions, demands, or criteria results are supplied.
- The pinned queue has T09 `active` and T10 `queued` with `depends_on: [T09]`. T09’s current first-action/phase record says solver inputs remain incomplete, 47 of 50 current wood identities are not meshed, and no reactions, joint demands, or accepted six-case responses are available. Thus the packet’s distinction between active T09 model integration and not-yet-produced demands is accurate; T10 has not supplied completed demands.
- Attempt09 is an imposed relative-port N+ diagnostic. Its frozen run plan is static, not a physical service history; the execution timed out before an accepted increment and has no accepted response. The post-run suggestion of a physical-mass transient is a possible numerical method only. The approximately 1.3 mm travel remains geometry-target language. The packet does not infer service demand or physical event time from either.
- T02 attempt09 remains an unrun capture-method coupon; its contract scope is output instrumentation. T03 attempt07 remains an unrun small static topology coupon. The pinned status records unavailable runtime and false readiness/authorization; fresh readiness, required authorization, durable parent-owned run-once tracking, serialized execution, and each coupon’s own pass remain prerequisites. Neither coupon is represented as joint acceptance.
- Only decision 1 is closed. Decisions 2 and 4–5 remain `UNRESOLVED`; decision 3 is source-bound only to attempt01 N+ A00–A03 and final freeze binding is unresolved. The ordinary-joint freeze remains `NOT_READY`. Top-level native execution, mechanical acceptance, new-load selection, and geometry-change flags are false. No run, geometry change, service-demand inference, or acceptance claim is made.

No substantive source/provenance or claim-boundary mismatch was found in this bounded review.

## Exact hashes

Packet files:

- `README.md`: `3a18de64843e971668049a1bd31d54508ee5587c6fdb066bcd88e82cc71c29f3`
- `decision-classification.json`: `116b39ca040569ae6008f2f89fe8b651b053da08f6b450641cee8846cb1e48f4`
- `source-pins.json`: `ef7858d84d6ec122cdfdf5c403efeaf80ccb075a46278d481e62786298b06aac`
- `SHA256SUMS`: `07dc7bbc55d47bcc8f0c1cd9189b1b72c12815f9612c38aaa942b7d4703e9872`
- `SOURCE-SHA256SUMS`: `3ace4e55685ba7b7bd3703bf5fe1bcb7ce5a8f07643e70200618c1a139deab00`

Primary bound sources:

- Six-case contract: `9c7c43c51ce635ebfeaeddabdbbe2a0ac80dfd7819ec357662dd132db648b83a`
- Full-frame manifest: `2f5eed3e4fa01e62e776d8fc0e4fae12182f86e1d84c63c956dbe7b44fbb5896`
- Current T09/T10 queue: `3b913c06143ee59bc7012f4e814ada43a01f7954a9963324dfb93ac85b3873f4`
- Current readiness/status: `691f942be7826dd7b07d178a1ba237b5ce3d9b5e9afe8dc3f81ebcaba1b6d6cd`
- Attempt09 run plan: `16008473b58e08aef3aa6cd73577132103968f8d97c17c9de27a571231845801`
- Attempt09 execution record: `1af13ed1d6d1506f2b15cbf7cfe8ba784ddc27b2372de4b2d3888f172eff27a6`
- T02 capture contract: `8de249a8429e43485c8ba5618ee0296fbb4ce3d551d908e9fb0e8a7be6a4a441`
- T03 coupon README: `647684313071cf283a1c25af6b821e98bfa2afb74ff3f2674617914653d9381d`
