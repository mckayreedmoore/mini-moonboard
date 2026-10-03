# STI17 and stress-frame architecture review

Review scope: source-only review of the STI17 build/coupon preparation packet and the rotated orthotropic stress-frame preparation packet on `master`. No build, compiler, solver, mesh, CAD, native artifact, test, readiness, freeze, ledger, or shared-source operation was performed. The packet READMEs report 11 and 16 synthetic tests respectively; those results were not rerun here.

## Finding

1. **P2 — The stress-frame reader still needs the parent-owned provenance wrapper before a native result can be used as a traceable known-answer.** `check_output.check()` accepts the raw DAT text, expected values, coordinates, and strain as independent caller arguments ([check_output.py](/home/mckay-linux/repos/mini-moonboard/docs/wood-joints-mvp/hypotheses/orthotropic-stress-frame-preparation-2026-10-01/check_output.py:38)) and returns a numerical pass status without binding those arguments to a freeze or execution record ([check_output.py](/home/mckay-linux/repos/mini-moonboard/docs/wood-joints-mvp/hypotheses/orthotropic-stress-frame-preparation-2026-10-01/check_output.py:133)). A caller could therefore pair output with expectations from a different prepared deck and still receive a numerical result. The README correctly discloses that the reader authenticates no execution or artifact provenance and that the wrapper is unfinished ([README.md](/home/mckay-linux/repos/mini-moonboard/docs/wood-joints-mvp/hypotheses/orthotropic-stress-frame-preparation-2026-10-01/README.md:47)). Keep the numerical reader pure; have the parent wrapper verify the exact freeze and its deck/oracle/source hashes, derive coordinates and strain from those frozen inputs, bind the raw DAT hash to the terminal execution record and run ID, then record those identities alongside the numerical result. Until then, the fixture remains preparation-only and supplies no native known-answer evidence.

## Architecture disposition

The STI17 packet has a clear ownership chain: parent readiness and an input freeze gate a one-copy build, the terminal receipt records the freeze hash and before/after source and object identities, and a separately prepared coupon freeze embeds the STI17 profile for the existing runner. Its bounded builder and coupon freezer have distinct responsibilities, while the old profile and base image remain separately identified. No other substantial ownership, coupling, or source-identity finding arose within this packet's declared source-only scope.

The stress-frame producer and numerical reader are also separated cleanly. The producer pins its mesh inputs and parent oracle and labels its output unfrozen and unexecuted; the reader checks the distinct global, local, and default output blocks and does not claim mechanical acceptance. The remaining issue is the explicitly unfinished provenance integration above, not a reason to add run logic to the numerical reader.

## Applicability limit

This review addresses module and artifact boundaries in the two preparation packets only. It does not establish solver behavior, readiness, freeze validity, mesh validity, native output correctness, or candidate mechanics. The README-reported Ruff and synthetic-test results are unverified by this review.
