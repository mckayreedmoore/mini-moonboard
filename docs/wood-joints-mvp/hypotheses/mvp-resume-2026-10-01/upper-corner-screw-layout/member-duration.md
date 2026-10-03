# Timber duration comparison

This finite comparison retains the original **250 lb × 2 downward load,
signed 300 N horizontal load and 100 mm front lever**. There is one saved
six-case force source. No climber load, elastic modulus, stiffness, contact
law, section geometry or hardware capacity is changed.

## Working assumption and primary basis

For this conditional MVP calculation, exposure to the complete rated dynamic
peak is assumed to total **at most seven days over the frame's life**. This
is a declared use assumption, not measured use. It concerns cumulative time
at the full peak; ordinary climbing hours are not automatically peak hours.
The corresponding timber strength factor is **C_D = 1.25**. The separate
[gravity-only comparison](dead-load-check.md) uses **C_D = 0.9** for the
permanent frame and original 25 kg equipment allowance.

[2024 NDS Chapter 2](https://web-media.awc.org/wp-content/uploads/2021/12/17210153/AWC_NDS2024_20231129_AWCWebsite_Chapter2.pdf),
Table 2.3.2 and §§2.3.2.1–2.3.2.3, supply these factors, permit the shortest
applicable duration in a load combination, and require the other applicable
combinations to be checked. The authenticated local source is
[the cached chapter](../../upper-block-strength-2026-10-01/source-cache/chapter2-2024-awc.pdf).
The normal-duration reference corresponds to approximately ten years of
cumulative full maximum loading. The
[AWC commentary](https://web-media.awc.org/wp-content/uploads/2021/12/17210642/Part02DesignValuespp7to19.pdf)
explains the cumulative exposure basis; the pinned 2024 specification governs
the arithmetic here.

This assumption does not assert that every possible intermediate sustained
load combination has been evaluated. The six rated states and permanent
state define this finite MVP envelope. Uses with greater cumulative full-peak
exposure require the corresponding lower strength factor. Original **C_D = 1**
results remain available, including the rail face exceedance; this document
does not rewrite their disposition or formal acceptance criteria.

## Calculation

[member-duration.py](member-duration.py) reuses all **34,704 bore-free signed
cuts**, six cases and 44 members from the frozen member stability worksheet.
The remaining 20,472 source traces retain their bore/terminal exclusions.
Each complete signed cut and its existing centroid correction are reused.

Only `Fb`, parallel-grain `Ft`, parallel-grain `Fc` and `Fv` receive 1.25.
`E`, `Emin`, perpendicular compression, steel and hardware remain unchanged.
Beam and column stability factors are **recomputed** with adjusted strength
and unchanged Euler references, lengths and restraint assumptions. The
normal interaction result is not obtained by dividing its old ratio by 1.25.

The unchanged shear helper first recovers its original transverse and
orthotropic torsion stresses against the original 180 psi shear reference.
The resulting strength comparisons receive the duration factor separately.
Original face and conservative component bounds are both retained. The
coefficient-5 comparison remains a separate sensitivity, as before.

The existing candidate timber restraint, prismatic section, aligned
orthotropy and parallel-grain shear allowance assumptions remain explicit.
Excluded holes, terminal profiles, unsampled stations, local joint cracking
and product qualification are outside this calculation. The factor supplies
no Hillman withdrawal, head-transfer or lateral capacity; those demands and
reference deficits remain in the panel worksheet.

## Parent execution

The parent executes `build(output: Path)` once in the serialized calculation
slot, using a fresh child of `rawlocal/member-duration/`. It authenticates
source hashes and reproduces every original applicable normal/shear result
before calculating the duration comparison. Original beam/column kernels
are also reproduced. Any mismatch stops the calculation.

Outputs are `checks.json`, `same-cut-states.csv`, `receipt.json` and the
executed producer snapshot. Global and per-case peaks retain their complete
same-state signed actions and section identities.

## Completed rated-case result

Parent executed `rawlocal/member-duration/parent-attempt01`. All original
applicable normal/shear values and stability kernels reproduce exactly
(maximum difference **0**). All 34,704 timber-restraint normal comparisons
remain inside their declared slenderness domain, with no checked exceedance.

| Frozen comparison | Original C_D = 1 | Conditional C_D = 1.25 |
| --- | ---: | ---: |
| Normal/stability peak with candidate timber restraint | 0.628421 | **0.518810** |
| Rail compatible face shear/torsion peak | 1.021524 | **0.817219** |
| Conservative all-section component bound | 1.189165 | **0.951332** |
| Coefficient-5 isotropic sensitivity, non-adopted | 1.318027 | **1.054422** |

The first three comparisons lie below their declared adjusted references.
The older coefficient-5 sensitivity remains above one; it is retained and
does not replace the compatible source-orthotropic stress calculation.
The original face exceedance remains recorded at C_D = 1.

| Artifact | SHA-256 |
| --- | --- |
| Executed producer | `4407e780ade7a5f4f08eb586b6aea15130a6dd81ef747f535562a812f4a10c6d` |
| `checks.json` | `50fcb02f05744d5d054bbc5d65aea07e92ef742497fc697ba6c9b31ad3a61623` |
| `same-cut-states.csv` | `75a594e5ea83cc18c01ee6c8d36daa7869ecfd12d5fea20ff6927862e2af07c5` |
| `receipt.json` | `144d422ecfa6b7d92b6ad2d6f3630fce84eadb2d63375c7d5395586fd0f95a4d` |

Runtime was Python 3.12 with NumPy 2.5.2 and SciPy 1.18.1. The source
baseline reproduction is explicit. No frame, CAD, native or software-test
run occurs in this saved-cut calculator.

## Permanent-load completion and conditional working decision

Parent completed the [gravity-only calculation](dead-load-check.md) at both
zero and nominal clearance, with original frame/equipment gravity and no
live load. All 88 member balances and 11,568 applicable cut traces complete.
At C_D = 0.9, normal/stability, compatible shear/torsion and component-bound
peaks are **0.174220 / 0.132797 / 0.181737**. All applicable normal checks
retain their declared domain. Permanent comparison SHA-256:
`20802196776a89ea8b041832b413ef8d8613493b1bf36f89a3810807c5166e75`.

For the conditional MVP working assessment, use C_D = 1.25 for the six
rated cases and C_D = 0.9 for permanent gravity, with the seven-day cumulative
full-peak assumption above. This completes this finite load-duration
comparison. The individual producers do not select an authority or update
formal gates; this parent working decision is recorded here after both runs.
The original C_D = 1 rail exceedance, non-adopted coefficient-5 sensitivity,
restraint/torsion limits and panel reference deficits remain visible.
Formal qualification, complete-joint acceptance and all physical-release
flags remain unchanged.
