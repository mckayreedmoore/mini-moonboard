# Independent post-run audit

I independently audited the frozen packet, run records, and raw native captures
for the three-case implicit current-map fixture. The frozen verifier reports
`PASS_CURRENT_MAP_KNOWN_ANSWER`; I reran its offline `--audit-dir` command
without `--write` and reproduced that status. I did not rerun CalculiX, freeze
the packet, or modify a frozen file.

## Freeze, source, and capture integrity

The freeze SHA-256 is
`36b624a9d4658862e96a225a28b844b8372150dc449e4749a4b683faf5adcf9e`; the
final acceptance is
`4aee8f74437640a2eb8a87f75c4fb70b16ce72a2e6df974a0f5f37406acb0ce3`, the
expected contract is
`88521d8367b2ea33c170c3c82a1a417b2fa481cf2afd7afc01558b0b7053172a`, the
runner is
`28f0d0221fb10e8e864b0c7c4fbb85e758586bfaf6bc4230d98650b1c215ae91`, and the
verifier is
`864ed594c7f324706c2308637e5cf4b25de8910ca6b4a54199fc55ec8b546e4a`. The
execution record SHA-256 is
`29e7705be56e655758c8133ee2cd3e5f5325b1ea3d2d98058fd1002702cac4b5`; the
verifier report SHA-256 is
`e9c2da08d7ff1bffdd8fcffbb06d921ab71472ec409494c91334e1767c506603`.

I rehashed every one of the 24 frozen local files and 14 external dependencies;
all matched `input-freeze.json`. The verifier binds the observed freeze,
execution record, expected contract, and case output digests. All 27 files
listed in the three `case-execution.json` output inventories matched their
bytes, with no unlisted output files. The pinned CalculiX binary hash is
`c6882d262b44525a563250673420dff1506c41b95e6d82d50392f9af26111863`, and the
image is `sha256:31336f517557f5dd5f97d85b1e6e15947fd1c10b44edc1364dbba4c1a5ab6c38`.
The pinned 2.23 source archive SHA-256 is
`9c88385c10fb04f5dc6c4e98027a51bebdd8aee3920e05190d6c1dd08357d6e7`. Its
four-point C3D10 mass/reference members are `e_c3d.f`
`d009650b48e5ca150080aed9e19d1b65d2b2cf4869ab6d7f2b1a5cd55e2df3fc`,
`gauss.f` `aed2d48b6a63e30894e747a531f6edc32e3cd921338e370902dfb62d8e304df2`,
and `shape10tet.f`
`747b5c03627053292f23e7a6f2d4e16ca75b12e33c7d7c48109eb7c91c5d449c`.
Rigid-carrier source members `rigidbodys.f` and `nonlinmpc.f` are respectively
`53c44c6aeb6cc08912ad9538cf592957ea13c44ba1bbe407a4adb94ee12d68ea` and
`a9331e1895c9bcea10c405bb05f75788f4d3a6b45022e54e6a338b69850f4036`.

The source/input freeze also pins the current mesh and map files; the
independent input audit checked the source geometry/connectivity, original six
shaft-fit equations, and all 22,696 serialized CLOAD rows. Its maximum load
component difference from its independently reconstructed vector was
`1.3962808739895107e-21 N`. This confirms the captured decks and source lineage;
it does not independently qualify all four current maps.

| Case | Case-record SHA-256 | Input | DAT | FRD | STA | CVG | Stdout |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `direct` | `201cd90087025a9c0bd8a6337c928d7d8479669fce82f4bfcc68c16da2a61a33` | `0f9ff1b41b5d44774bd8d9da049f85d7e8c452a523c4ada99ab56a25b0fb0d94` | `9664bd44962ea9486b8fb45c693c8b41b59a916667f99278d990c70d22926d1d` | `63cc95a323f77b5dcec9fad72392182c9fc8f1c1a2f71b1ee3d21edbccc24ed3` | `b3abd4dffd5bfda45c31c525a91097e9f3660eabe6dc784c5bb128253540f082` | `8f1093ab0176f268f3dcf7b6bf384af81ad633d585fcc3c81b1237ea12f3d5e0` | `78d4588d8c5d93d1e1296b982b8fafda23f5f0072efe46b7d66287689cd0ea08` |
| `mapped_no_carrier` | `c78a25f3df832d13ea204b37bf415ea273827b125a3f654ae9da169a70b87cb4` | `fc3bc4c04477979c27375f414c130687bee97181c795d3c6ea3ed37aceab80bb` | `0e99184b492c0339724b4e938446090d650b7eb0e018d141222e086f9f08fedc` | `07b939e3ff6c88960fb5262ea5aff0e4bd6b0dd2ef1fa34d58cb484dc455f913` | `b3abd4dffd5bfda45c31c525a91097e9f3660eabe6dc784c5bb128253540f082` | `d30c9ef8828198403d9fd16bf47ff138734156e99584d244a137af8b0500df06` | `90777a8527fe74b38fa9a4ee43264b3b554a7705dfd516e1d116ac7d6e85c91d` |
| `mapped_carrier` | `9933906ad66f4e6f7b2707ad836e0d3017dc51bff51c9bf83f1e70f9b5641eb7` | `73eacc181ebd37efe63a10a5e7822e0d5cbc7ae9ce23446185c9f5f6456b620e` | `770fe86eea0f1e98507f6e3ab7a34f1d8104bc17cc3ce4ec0a580e83b7b33c31` | `0ff8f0ea7a13fe6d239dfe9091def1433a5f706126bfe8447b592ac225403c7a` | `b3abd4dffd5bfda45c31c525a91097e9f3660eabe6dc784c5bb128253540f082` | `c69d458a061445d56fea704d55064f43e268262016fab7ef71da8dfe96b404d2` | `37ef098efc4dc07cac75d2d45c340cea0136627651d208b5517186c1f0c0bbef` |

For all three cases the omitted `coupon.12d`, `solver.stderr`, and `spooles.out`
files are empty and each has SHA-256
`e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`.

## Raw result audit

I parsed each raw STA, DAT and FRD capture using the packet's pinned parser
dependency (`explicit-c3d10-mpc-known-answer-attempt01/verifier.py`, SHA-256
`e42c5e0b9ced533b461bc984e39d7a0d5081c45ddb1022206251bf7fbe909620`). Each
case has ten accepted rows at 0.001 through 0.010 s, one attempt per increment,
two iterations per row, no cutbacks, and matching DAT/FRD state times. All
requested fields parse without errors, and each solver stdout has one normal
completion marker. The mapped cases contain all six source equations and two
REF/ROT controls; unmeshed controls are present in DAT and correctly absent
from FRD.

| Case | DAT nodes in each U/V state | FRD nodes in each DISP/VELO state | Runtime | Native output bytes |
| --- | ---: | ---: | ---: | ---: |
| `direct` | 11,348 | 11,348 | 13.283884 s | 24,717,801 |
| `mapped_no_carrier` | 11,350 | 11,348 | 18.906411 s | 24,719,917 |
| `mapped_carrier` | 12,457 | 12,455 | 20.108165 s | 27,133,306 |

The execution intervals are serialized, with no overlap. Every container
exited 0, none was OOM-killed, stderr is empty, and each capture stays below
the frozen 120-second and 64-MiB limits. The case start/end times and output
byte counts agree with the execution records. The aggregate execution status
`CAPTURES_COMPLETE_PENDING_VERIFICATION` is the pre-verification runner state;
the separate later verifier record supplies the passing disposition.

Every reference, equation, control, carrier and parity gate passed. Across the
mapped cases, the largest six-equation residual was `1.5811155657138833e-12`
with a largest normalized allowance ratio below `0.476`. Maximum carrier
kinematic errors were `4.998688571848311e-13 mm` and
`5.1288892539491995e-11 mm/s` in DAT, and `5.023189836080919e-12 mm` and
`5.128453135793722e-10 mm/s` in FRD. Direct-to-mapped-no-carrier physical DAT
differences were no larger than `1.01e-19 mm` and `1.01e-16 mm/s`; adding the
carrier changed common physical DAT by no more than `1.01e-12 mm` and
`1.01e-9 mm/s`. All are within the limits that were frozen before execution.

The positive-mass bolt body has terminal printed mass `4.208483e-5 tonne`,
volume `5361.125 mm^3`, ELKE `2.768962e-10 N mm`, and near-zero ELSE. The
zero-density carrier has printed mass `0`, ELKE `0`, and volume `741.7892
mm^3`. Its ELSE is not exactly zero: the largest absolute value across the
ten states is `4.853587e-25 N mm`, within the frozen `2.7690623878091544e-16
N mm` allowance. This is a small numerical residual, not positive carrier
mass or kinetic energy. DAT also prints NaNs for the M03 center of gravity and
centroidal inertia, which are undefined zero-mass auxiliary statistics; the
acceptance contract explicitly excludes those two fields while requiring all
nodal U/V, control U/V, ELSE, ELKE, EMAS and EVOL channels to be finite. The
required fields are finite and complete.

The parent `RESULTS.md` summary agrees with these raw records and the terminal
report: the M03 ELSE is identified as small but nonzero; mechanical acceptance,
joint acceptance, and release remain false. I found no contradictory output,
hash mismatch, or basis to relax a gate.

## Bounded disposition and next question

This is a successful observed-method qualification for the one actual
`M00_A00` shaft-fit coefficient set, a small global-Y rotational forcing, the
tested 0.001-s implicit schedule, and its `M03_A00` zero-density rigid
carrier. It checks one elastic C3D10 bolt-body response against a predeclared
nearly-rigid reference; it is not a proof of an elastic-error bound, a contact
or joint-capacity result, or acceptance of the current joint.

Before an ordinary-joint solve, resolve the specific untested-set question:
the current A09 nut-coupling packet has four actual bolt maps with equation
row sizes 754, 775, 763, and 778 terms, while this fixture tests only the
first A00 map. Identify which of the other A01–A03 map/load-axis combinations
the proposed ordinary-joint case actually exercises, then either document
their exact rigid-coordinate equivalence to A00 for that observable or qualify
only the distinct active map(s) with a matching physical-versus-mapped
control/equation observable. Do not transfer this pass to the remaining maps
or run a generic coupon series without that demonstrated need. The current
test changes no contact-method gate or full structural criterion.
