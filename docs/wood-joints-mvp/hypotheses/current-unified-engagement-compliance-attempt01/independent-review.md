# Independent review: conditional Unified engagement scenario

**Reviewed:** 2026-09-25. **Result:** no material numerical or applicability
correction needed. The artifact is a reproducible conditional model scenario
and historical ideal-fit comparator; it does not establish a physical
1/4-20 thread-pair law, hardware fit, stiffness bound, or capacity.

## Source and numerical check

The primary [Matsubara and Teranishi paper](https://link.springer.com/article/10.1186/s10086-022-02038-1)
prints `K_th = A_s E_b / L_th` in Eq. (5) and `L_th = 0.85 d` in Eq. (9).
Its Eq. (4) places `K_th` in series with non-engaged thread length, bolt
cylinder, and bolt head; the joint model then places the bolt stiffness in
series with washer embedment. The paper identifies `A_s` as an effective area
from JIS B1082. Its tests use M12 SWCH bolts and report aggregate timber-joint
tightening stiffness, compared with that series model; they do not isolate
`K_th` or validate a Unified 1/4-20 matched pair. The README and machine
record state this distinction accurately.

The NBS Unified tensile-stress-area expression is an explicit substitution
for the paper's JIS area input, not a source-validated elastic area for thread
flanks. Recalculation from `D=0.25 in`, `n=20/in`, `E=200,000 N/mm²`, and
`L_th=0.85(6.35 mm)=5.3975 mm` gives `A_s=20.5296315 mm²`,
`K_th=760,708.902 N/mm = 760.708902 kN/mm`, and
`1/K_th=0.001314563 mm/kN`. The inch-to-mm area conversion and force/length
units are consistent. This is one equivalent model component after a flank
is seated; the result does not stand for whole-bolt or whole-joint stiffness.

The compliance partition properly keeps that component separate from the
bolt body, nut body, washer seat, and timber. Use the `K_th` connector only
for engagement deformation omitted from the explicit model; do not duplicate
it with explicit thread/contact deformation or a segment already represented
by the bolt/nut model. The source's `K_s` is the spring for the non-engaged
threaded bolt length, not flank backlash. The artifact labels both points.

## Fit comparator and scope

The H28 comparator uses historical 1/4-20 UNC 2A/2B pitch-diameter limits
and the ideal 60-degree relation. Under fixed relative rotation, the reported
clearance extrema give total reversal travel of `0.0161307–0.1422435 mm`.
This agrees with the predecessor calculation and its independent review
([fit review](../thread-fit-travel-attempt01/independent-review.md), whose
calculation input is pinned below). No factor-of-two correction is needed:
the input is diametral pitch-diameter clearance and the ideal axial reversal
is clearance divided by `1.7321`. With an unknown initial phase, one-direction
free travel of zero to the full reversal interval is correctly kept distinct
from a centered half-gap. Free relative nut rotation couples axial advance to
the helix, so this fixed-rotation interval does not bound travel when the
hardware can turn.

The text consistently labels H28 as historical, requires current B1.1
numeric limits or part-specific profile evidence before physical acceptance,
and leaves delivered class, full-form overlap, chamfers/runout, initial phase,
and rotation/end-stop state unresolved. Its piecewise equation is explicitly
a combined conditional diagnostic, not a physically validated constitutive
law. The M12 composite tests and nominal stress-area substitution do not
convert the tangent or H28 interval into a 1/4-20 hardware guarantee. No
claim of preload, thread strength, stripping resistance, or capacity appears.

## Reproduction and pins

Ran `python3 -m unittest -v test_calculate.py`: all 5 tests passed. A
read-only comparison of `build_calculation()` with the checked-in JSON was
exactly equal; it reproduced `K_th=760.708902392208 kN/mm` and reversal travel
`[0.016130708388661014, 0.14224351942728458] mm`. No producer rewrote the
result.

| Artifact hash at independent review, before later style-only cleanup | SHA-256 |
|---|---|
| `README.md` | `1a37e07f4c12ff8282e992b3d105ce677e0b529ba574ec2362a94ad169996d78` |
| `calculation.json` | `9b52458dad92d5f4c4c452ef36ba4567b168c9a175c86ab02632a0d1edf1ca47` |
| `calculate.py` | `db50430857cb69e3d1bc5c394a90e3229642fdbea18574a0ccd8fff5b4df5a8e` |
| `test_calculate.py` | `e27fd48596bdfffc3b3314a93e610abd8052e7e5811fa4abe7f09e40980a5bfd` |

## Parent-authorized style-only follow-up

After this independent review, the parent authorized Ruff import ordering and
formatter-only changes to `calculate.py` and `test_calculate.py`. The changes
are limited to import organization and whitespace/line wrapping; the numerical
operations, pinned inputs, assertions, and applicability claims are unchanged.
At this style-only update, `calculation.json` retained its original hash; it was
regenerated only in the contextual-pin follow-up below. All five focused unit
tests passed again, and Ruff lint and format checks now pass. A read-only
rebuild from the pinned inputs compares exactly equal to the stored JSON.

| Artifact immediately after style cleanup, before contextual-pin removal | SHA-256 |
|---|---|
| `calculate.py` | `790cbca3f3828ec7cbbc4ccd3b1054c616bc51bdd3a8540f2373295bf9a664c3` |
| `test_calculate.py` | `6a30f308be506f52b26315b39b0a3835c5e84d0aa44808821c1ff9404fabba73` |

## Parent-authorized contextual-pin removal

After style cleanup, the parent identified
`docs/wood-joints-mvp/current-engagement-model-applicability.md` (SHA-256
`5e5e530b45812519e6e8dc6811bee740cd717b3b8ffe2cba5070f83691645305`) as an
untracked contextual summary, not a numerical input; it also links to an
unreviewed appendix. The parent authorized removing only that entry from
`SOURCE_PINS` rather than adding the unfinished contextual document to this
completed chunk. The eight remaining pins are the calculation's source-bound
documents/data artifacts. Before regenerating the JSON, a read-only comparison
confirmed that removing `source_pins` from both the prior and rebuilt objects
left every other field exactly equal, and that the other eight pins were
unchanged. The pin count test, focused unit tests, Ruff lint, formatting, and
read-only rebuild were then rerun.

This follow-up changes only the source-pin list. It does not change equations,
input numbers, numerical outputs, conditional applicability limits, or claims.

| Current artifact after contextual-pin removal | SHA-256 |
|---|---|
| `calculate.py` | `76ff6e064ae7aa199d9b13c67be40a4b2f1fe00961f81c559c65fb74b0845c68` |
| `calculation.json` | `13d8995c3d855f3098cc6613e0ca04218835346e22cc657fcf9cc0b0ae06ee88` |
| `test_calculate.py` | `793dcf12e4d4a971f92a086a31836ce0566ac574c67d01d7523530ce03102a2d` |

The producer binds eight local documents/data artifacts, including the
preceding [nominal tangent calculation](../current-engagement-analytical-attempt01/calculation.json)
(`80f73199d77e7d6147d6e4d8a74018c151a45a89070882c6c888a5440d0b44eb`) and
[H28 travel calculation](../thread-fit-travel-attempt01/calculation.json)
(`206ff1dae7d83b739d5af909e27309b2d8e2f1dda399c190f07a4def9898c43b`).
