# Bottom-outer finished sections: independent calculation review

## Result

No substantial source-join, sign, couple-transport, half-body boundary, or
rounding defect was found in the reviewed replay. The standalone oracle
reconstructed the four bottom-left bolt axes and eight receiver memberships,
placed six grain-normal planes, and matched all 63 whole-body states and 252
two-trace cuts against the producer replay. It independently joined physical
connection forces, exact floor tangents, and load-factor-scaled nodal body
loads from the three frozen families. It compared point-action identities and
side ownership as well as force, moment, propagated rounding radii, local
components, and transport to each reported finished-area centroid.

The six planes resolve to three current finished STEP bindings. For each
member, the frozen model geometry descriptor, feature-register binding, and
SHA-256 of the saved STEP bytes agree. Each reported section centroid lies on
its reconstructed plane; reported component areas sum to the reported net
area. The oracle also confirms the README's statement that every plane crosses
at least one finite source contact-patch station extent. The exact planar CAD
extraction remains covered by the separate
[finished geometry review](finished-geometry-review.md).

This result validates a conditional point-action demand join. It does not
establish integrated section traction, compatible deformation, load sharing
between disconnected regions, resistance, a strength pass, joint acceptance,
physical inspection, or fabrication readiness.

## Independent replay

Run the verifier with its default local replay path or supply another report:

```sh
python3 docs/wood-joints-mvp/hypotheses/bottom-outer-finished-sections-2026-10-01/parent_verify.py \
  --report /tmp/mini-moonboard-bottom-outer-finished-sections-2026-10-01.json
```

The verifier imports neither `produce.py` nor the upper point-action or CAD
extraction helpers. It reads the raw frozen JSON records, independently
reconstructs signed point wrenches and componentwise uncertainty radii, and
checks complete positive- and negative-side action partitions for both
one-sided cut traces. A small known-answer check covers the cross-product sign,
datum transport, and uncertainty-radius transport. The verifier rejects
changed pinned inputs, candidate or revision mismatches, incomplete or
duplicate report rows, and missing state, plane, member, or bore identities.

The run passed on October 1, 2026:

- Three families × seven increments × three members: 63 whole-body states.
- Three families × seven increments × six planes × two traces: 252 cut states.
- Four axes, eight source bore memberships, six distinct planes, and three
  byte-verified finished STEP bindings.
- All six planes cross a finite contact-patch station extent.
- Independent known answer: pass. `ruff check` on `parent_verify.py`: pass.

The replay JSON stays in `/tmp`; this review publishes source hashes and
coverage only. No CAD extraction was run by this calculation reviewer. The
existing handoff records 16 passing `test_sections.py` checks and Ruff for the
producer/test work; those checks were not rerun here. The separate testing
review notes that this suite does not invoke `produce()` or assert its full
emitted identity and claim-limit coverage. That is a regression-coverage gap,
separate from the replay calculations checked here; an integration test is in
progress in the parent-owned review sequence. The
[resistance disposition](resistance-disposition.md) keeps bolt, wood, contact,
and complete-joint resistance open. Its quarter-inch/45-ksi lateral ratio is
explicitly an unadopted scenario and is not recalculated or promoted here.

## Reviewed identities

| Artifact | SHA-256 |
| --- | --- |
| [`produce.py`](produce.py) | `662404918c93bb9d96fa48b0b9f02237aaf260b8db1c510dfe866334017e4da7` |
| [`test_sections.py`](test_sections.py) | `2632083c4e393b0d212426522405463f642f11cf488155a50617579eb6517aad` |
| [`parent_verify.py`](parent_verify.py) | `c458e0d74ddfe4042c7f7071741c67f3c36d66e53cde7e60444ffc4299fe7dbf` |
| [`host_actions.py`](../upper-outer-load-path-2026-10-01/host_actions.py) | `39b3af2bdd468d20db868454cb81cce1ad2d3af30059c4204aa2284892cd390b` |
| [`section_geometry.py`](../upper-outer-finished-sections-2026-10-01/section_geometry.py) | `8672daac3cef4aa55641a3e1bf6cee636d779be48145858282ffb0ed4d76f8d3` |
| `docs/wood-joints-mvp/hypotheses/current-finished-feature-register-2026-10-01/axis-features.json` | `bebb4274cdecfb6ad0b0f26850d85a16570c245ea9f7d478c0b05c12b4513e19` |
| `docs/wood-joints-mvp/hypotheses/upper-frame-joint-review-2026-09-30/freeze.json` | `d4ba1c78eb358d25e32819201e9c59e05d425a06d9e4e5cca3dc09d7139ffd73` |
| `docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/reduced-static-attempt01/contact-geometry.json` | `034067430fff5207cdb40819fa8118a367edeb29a8d83926928cc96a0e87d151` |
| [`finished-geometry-review.md`](finished-geometry-review.md) | `b0b6d281a604e8ea9db6897e3838e077c768f750255f86915c412d2aa7558029` |
| [`method-review.md`](method-review.md) | `54cc0b7e72482cb63954468d9d58438ee0be3c97da92ffe0e66079a870b868a8` |
| [`README.md`](README.md) | `4692844352fa3cdf48be1b45fd49372b5337e56996cdad156427529bbb08f7e2` |
| [`resistance-disposition.md`](resistance-disposition.md) | `39945e0cd3cfc2cc904d3880ae3019db6a92bd0512af075d0316700e937ae066` |
| [`testing-review.md`](testing-review.md) | `42b254d808545d7fdf9c83f418411b5bc1f24366cadf82b48161a5f74a81316f` |
| Full producer replay at `/tmp/mini-moonboard-bottom-outer-finished-sections-2026-10-01.json` | `4303d229d154708a0356924d42b9daab8df78314f40d3e2d8d165ad209cbf6b8` |

The independent verifier pins the producer, both reused methods, the feature
register, freeze, and contact-geometry inputs to the hashes above. It also
checks every file entry named by the frozen case records before calculation.
The freeze SHA therefore identifies the exact per-case model, response,
all-body audit, and auxiliary frozen artifacts used by the run.

The three finished solid identities verified from both feature bindings and
frozen model descriptors are under
`docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-full-frame-member-solids-attempt01/bundle/members/`:

| Finished member STEP | SHA-256 |
| --- | --- |
| `base_rail_bottom_left.step` | `724d46fa7902a949b79b0fd6132c5e57c580be80aad7d059c29e04494ff79923` |
| `base_side_left.step` | `237c3fa6aa0b52c39124580810d048e38919b99b9a1fb5db5a2423e7eda62fdf` |
| `bottom_outer_left_cleat.step` | `28d1b5fee748c38e30e3d2618c8377cfe374c7ccd0b520736c25841720824438` |

Frozen model/response/all-body-audit identities checked for the three case
families:

| Family | Model SHA-256 | Response SHA-256 | All-body audit SHA-256 |
| --- | --- | --- | --- |
| `a1-rear` | `72d043e1a70702d8d464c21a039e897036e17c95e368ec776063584dac74f5fd` | `257b5b743369fcc2242537b7ccfe81f2efba0a195ef044624d7b67da6a09678c` | `247845921630a092c3f7a79d9ac11c92d732f021d2cb1dc5214e54b1a344deca` |
| `a12-rear` | `8a90452d8afa1f1722b3253b18d5aeec72c432033a22d5d0828082022cc1cda8` | `892dadeed0b20d809ce5250d3cd1c3deb31697f69208d8bbefb5f702160e1274` | `3da26086016c01f830e055bfa72c8a55370c9adc138b28d73127596924c410d5` |
| `k12-rear` | `8f1d9bce9b62b18b3694f81816ef5c4c7cbe5e94b4c459a640fce7a98db68dbd` | `42ffb135d47bd3bd28874e886682b4f07175ee060fb383b6e3c128e5102073c6` | `66c2b9aa397b16cd4c0b2420c5cf4588e15d12bfd3fbfd75b7df8f2b0d1d4bee` |
