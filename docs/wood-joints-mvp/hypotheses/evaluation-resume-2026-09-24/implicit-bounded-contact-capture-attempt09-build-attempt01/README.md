# Attempt09 pinned production build — attempt01

This append-only build attempt stages the exact attempt09 CalculiX 2.23 source archive, additions-only patch, patch-preparation record, inherited upstream build manifest, original base-image pin, and upstream Makefile in a fresh context. A parent host wrapper checks the original tag against its frozen image ID, assigns that image a unique digest-labeled local alias, verifies the alias, builds with that locked alias, no pull, no cache, and no network, then verifies the base layer prefix and post-build tags.

The build recipe is adapted from reviewed attempt04 build code. The recipe changes are the attempt09 patch-preparation schema (`v9`), a unique dedicated binary path, and attempt09 wording in its error text. It verifies all 1,197 archived source-file hashes, the three attempt09 patched-source hashes, the additions-only patch hunks, original executable hashes before and after, and required capture symbols. The image-local build manifest binds the original source pin, the unique locked base reference and ID, and every build-context input. The host wrapper extracts the binary and build manifest from a created-but-never-started container and compares their hashes.

Scope is production compilation and provenance only. No native solver case or current-joint model is run here. Coupon launch requires a separate exact freeze, fresh readiness and run-specific authorization, and a consumed parent-ledger reservation before the serialized one-case run.

Exact base image: `mini-moonboard-fea:ccx-upstream-2.23-v1`, ID `sha256:31336f517557f5dd5f97d85b1e6e15947fd1c10b44edc1364dbba4c1a5ab6c38`. Attempt09 source pins: `attempt09-source-pins.json`. Run `python3 build_attempt.py` only after independent review of the pinned context.
