# Independent half-step input launch-gate review

**Finding: input gate passed for the frozen 0.5 ms derivative.** This review
covers input lineage and launcher compatibility only. It does not assess solver
results, time-step convergence, contact acceptance, or joint mechanics. The
parent owns the serialized native launch and any output review.

The child at
`ordinary-transient-seating-100n-every-increment-k1e4-halfdt-attempt01` is
bound by input-freeze SHA-256
`ea24423f587795743d0c1189c798f77d83159208c76d5d1d3a9fa5554eda4f56` and pilot
SHA-256
`1763d0ad15c2d53d86bdcf25ea136f3a3d267739b682d0dcd5d3cb2167387485`. Its
parent-pilot matches the frozen 1 ms pilot. A direct comparison finds exactly
one changed line, line 113 under `*DYNAMIC,ALPHA=0`:

```text
0.001,0.025,1e-06,0.001
0.0005,0.025,1e-06,0.0005
```

The end time remains `0.025 s`, minimum remains `1e-6 s`, maximum and initial
increments become `0.0005 s`, and the step remains adaptive implicit with
`ALPHA=0` and `INC=10000`. All 27 parent artifacts have matching child copies
and hashes. The child freeze contains 34 total artifact pins; each pin matches
its file. The generic transient launcher validates every file in that map and
has no fixed artifact-count restriction. I exercised its pin and command
preflight using a temporary symlinked copy with Docker and `Popen` mocked: all
34 pins passed, and no container or solver was invoked. The prepared child was
not modified.

The change preserves the 662 serialized CLOAD terms and 101-point RAMP_N table,
all 35 contacts, and all 41 every-increment output cards with `FREQUENCY=1`.
The frozen parent artifact map confirms the mesh, materials, nut coupling,
contact, and output inputs are inherited. The included decks contain no new
boundary restraint, spring, dashpot, or external load card. The packaged solver
image remains `sha256:5adec98a0bb4f4cffbcc3fa15f5014db08621f1204b65cf1f130ff46d9cd32b0`;
the child lineage and transient launcher pin the same `/usr/bin/ccx` SHA-256
`6adaabf5bf0382fc2bfd692b984320ed375dba777f7dc8297562f818043faa1b`.

The coarse parent was deliberately stopped after 38 accepted increments. Its
last accepted status token is `0.217118E-01`; it has no `0.025 s` endpoint, so
the half-step case can provide its own endpoint but no coarse-versus-half
comparison there. For `.019` and `.020 s`, the expanded parent contact-storage
audit maps all 35 manifest pair identities and has matching CNUM, CDIS, CSTR,
and mapped row counts at each endpoint (108,297 at `.019 s`; 72,155 at
`.020 s`). Its parent reproduction matches and independently recomputes all 35
pairs. This supersedes the earlier partial/missing 20-state report only for
those two audited endpoints; it does not supply missing results at other times.

The producer tests pass (`1 passed` in the focused pytest file). The reviewed
child freeze remains `FROZEN_NOT_EXECUTED` and explicitly withholds mechanical
acceptance. No half-step solver output is reviewed here.

## Pins

| Artifact | SHA-256 |
|---|---|
| Half-step producer | `dd8be8235d2b0e48a066d4b1015afc77fad26eadd44234348e10c3613d893d11` |
| Focused test file | `5c505261bce014786ad66d14e45a25c80de47f8bfe211f63c796d71ef98a3fc6` |
| Coarse parent input freeze | `f054d6b911fb0d9c9b0a183fa007d16d8a34a422904fd5cbcf73634e87797e66` |
| Coarse parent execution | `0b1c9721d23be5a85e7d0c10be924e70a15f080d47b6cc186178424e82d6f602` |
| Parent-directed stop record | `0fa4c34611a345410226849849733af101fc74b359462d94dc0a134a1c19e90f` |
| Expanded contact-storage bound | `909deb3929b6c97d0889363eae1fb8726a22c7e35ca975f4295ab91e79f38f16` |
| Contact-bound parent validation | `0515b6e8ff2add30cc982cf489073130e20ecd59812fe5ccb7ba76f644e0b483` |
| Half-step input freeze | `ea24423f587795743d0c1189c798f77d83159208c76d5d1d3a9fa5554eda4f56` |
| Half-step pilot | `1763d0ad15c2d53d86bdcf25ea136f3a3d267739b682d0dcd5d3cb2167387485` |
