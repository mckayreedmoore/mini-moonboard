# Stress provenance checker correctness review

## Input pins

Read repository `AGENTS.md` and target manifest. Target SHA-256 matched:
`e27297f27f2e1941c75adf571d482eeb8605c063c673bcc37c7af60168277226`.
All eight manifest-listed inputs matched declared SHA-256 and byte size:

- `check_provenance.py` — `6791c0c12a845a1b60d46a840a137b8c8827de1940e2436b2cbde5b452ebfb32`
- `test_provenance.py` — `3de48b526d10e055752276bf898f8f6242683a178f7fca5314678059bf248f78`
- provenance `README.md` — `cfdb2ea8e5212c483dc051ae2e3dbc3b9727c3e3609eb92c8d637043fa09c8da`
- `prepare.py` — `2a59e0700c7701022ecfeea4a77d47864c934df75dcf4fec7c480a6854de9821`
- `check_output.py` — `5d084afe311a1b836d1205240c063d9362554b73170d18adf86864dd03d4966c`
- parent oracle JSON — `1e82a2869b3609558024a3299363859f88e9d62c5770bacb26f92b4dfce5f5ff`
- `fea/wood_joint_reduced_native.py` — `ff7a81bc604090a4791eb584f9998bc76a35be2ac3ebaed15be970291583ff61`
- solver profile JSON — `f233cb12fe58983e968600befe78cc5ee0785903d60541a6269fe45e8489689c`

## Finding

**P2 — Boolean `false` is accepted as successful process exit.** In
`check_provenance.py:212-219`, `execution.get("returncode") == 0` accepts JSON
`false`, because Python evaluates `False == 0`. A hash-consistent execution
record and ledger can therefore pass the successful-terminal gate without a
numeric zero return code. Same type confusion lets JSON `true` satisfy the
ledger's `max_launches == 1` and `launches_consumed == 1` checks at lines
245-246. Require exact integer types (`type(value) is int`) before comparing;
add synthetic rejection cases for both boolean values.

## Limits

Reviewed checker, synthetic tests, contract, unchanged producer/reader, oracle,
runner source and profile. Source shows 22 cases (happy path plus 21 mutations);
parent reported Ruff pass. Did not run tests or other checks. No source edits.
Production freezer, scoped launcher, production freeze/run and native readiness
remain pending and outside this review; their absence is not a finding. No
native or host-attestation claim made. Parent retains acceptance authority.
