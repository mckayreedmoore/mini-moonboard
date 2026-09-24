# WJ-04 thread-root lateral-yield reference

**Status: conditional hypothesis only.** This note preserves a one-bolt
wood-to-wood lateral-yield calculation for the current WJ-04 full-4×4 cleat
geometry. It does not establish actual force, per-bolt demand, group resistance,
complete-joint capacity, or acceptance. It sits under `hypotheses/`; no
active evidence or manifest was changed.

## Candidate inputs

| Input | Value used |
| --- | --- |
| Candidate interfaces | Rail-to-cleat and principal-to-cleat, at candidate WJ-04 stations |
| Wood bearing lengths | Cleat 88.9 mm (3.5 in, treated as main member) + host 38.1 mm (1.5 in, side member); 127.0 mm total; zero gap assumed |
| Wood | Solid DF-L No. 2 assumption; assigned `G = 0.50` |
| Candidate axes | Rail bolts along `T`; rail grain `X`, cleat grain `N`. Principal bolts along `X`; principal grain `T`, cleat grain `N`. Each bolt axis is perpendicular to both member grains |
| Physical angle samples | Grain vectors are orthogonal in each bolt’s lateral plane. Common lateral force therefore gives complementary member angles; sample `(0°, 90°)`, `(45°, 45°)`, and `(90°, 0°)` only |
| Nominal bolt | `D = 0.250 in`, 1/4-20 UNC candidate |
| Thread-root scenario | `Dr = 0.189 in`, standard-based input for a 1/4-20 UNC external thread; not a delivered-part measurement |
| Fyb cases | `106 ksi` conditional commentary estimate; `92 ksi` analyst sensitivity only |
| End-distance scalar | `C_delta = 0.6063`, shown separately only for the conditional 26.95 mm / (7 × 6.35 mm) tension-parallel-to-grain end-distance screen at the upper crosscut cleat |

The upper crosscut geometry source reports the 26.95 mm rail-row end distances
and 33 mm pitch. Grain vectors and candidate stack dimensions come from the
[upper G7 crosscut hypothesis](wj04-upper-g7-crosscut.md) and its
[geometry producer](../../../scripts/wood_joint_wj04_upper_g7_crosscut_probe.py).
The 0°/90° endpoints are not actual signed-load classifications. No WJ-09
per-bolt signed demands are supplied here.

## Diameter and bearing convention

NDS-2024 §12.3.7.1 specifies the effective diameter used in Tables 12.3.1A
and 12.3.1B; §12.3.7.2 permits nominal `D` in lieu of `Dr` only when
thread-bearing length does not exceed one quarter of full bearing length in
each member holding threads. Actual thread transition and bearing lengths are
unresolved, so `Dr` is the conservative diameter scenario for the yield
equations and dowel moment.

The cited diameter clause names Tables 12.3.1A/B, not the wood-bearing values
in Table 12.3.3. To avoid silently resolving that scope, calculations below
show two **unadopted** thread-root conventions:

- **Nominal-`D` bearing input:** obtain `Fe` from the nominal 0.250-in
  Table 12.3.3 branch; use `Dr = 0.189 in` for the lateral-yield equation
  diameter, bearing term `Fe × Dr`, dowel moment, and Table 12.3.1B factor.
- **Root-`Dr` bearing input:** use the existing helper convention, which
  also selects the `D < 0.25 in` bearing branch from `Dr`. This is a
  sensitivity, not an adopted interpretation of Table 12.3.3.

For the conditional `D = 0.250 in` comparator, nominal `D` is used for both
Table 12.3.3 bearing values and the yield equations. This comparator is
available only if the member-specific §12.3.7.2 thread-bearing condition is
established; nominal 127 mm grip alone does not establish it.

## Sampled reference results

Values are unadjusted one-bolt NDS lateral-yield reference outputs from the
three physically compatible angle samples. `C_delta × value` is a separate
conditional scalar display, not an applied design factor or capacity.

| Bearing convention | Effective equation diameter | Fyb case | Sampled unadjusted range | Governing modes in samples | `C_delta ×` range |
| --- | ---: | ---: | ---: | --- | ---: |
| Nominal-`D` bearing input | `Dr = 0.189 in` | 106 ksi estimate | 158.276–175.862 lbf | IV (3/3) | 95.963–106.625 lbf |
| Nominal-`D` bearing input | `Dr = 0.189 in` | 92 ksi sensitivity | 147.453–163.837 lbf | IV (3/3) | 89.401–99.334 lbf |
| Root-`Dr` bearing input sensitivity | `Dr = 0.189 in` | 106 ksi estimate | 153.262–170.291 lbf | IV (3/3) | 92.923–103.247 lbf |
| Root-`Dr` bearing input sensitivity | `Dr = 0.189 in` | 92 ksi sensitivity | 142.783–158.647 lbf | IV (3/3) | 86.569–96.188 lbf |
| Conditional full-`D` comparator | `D = 0.250 in` | 106 ksi estimate | 189.348–219.996 lbf | IIIs (2/3), IV (1/3) | 114.802–133.384 lbf |
| Conditional full-`D` comparator | `D = 0.250 in` | 92 ksi sensitivity | 183.715–214.022 lbf | IIIs (2/3), IV (1/3) | 111.387–129.761 lbf |

Ranges cover only those three sampled angles, not every direction in the
continuous angle interval. The preserved
[JSON matrix](wj04-thread-root-lateral-reference.json) records the earlier
independent 0°/90° grid. Its 0°/0° and 90°/90° pairs cannot occur for these
orthogonal grain vectors; do not treat its independent-grid maximum as an
attainable candidate result.

### Reproduction

Run from repository root. This calls existing equation and DF-L bearing
helpers. The two thread-root bearing conventions stay explicit:

```sh
uv run --no-sync python - <<'PY'
from fea.dowel_yield import single_shear
from mini_moonboard.bolted_timber_checks import dfl_dowel_bearing_psi

modes = ("Im", "Is", "II", "IIIm", "IIIs", "IV")
angles = ((0, 90), (45, 45), (90, 0))
cases = (
    ("nominal Fe / root yield", 0.189, 0.250),
    ("root Fe / root yield sensitivity", 0.189, 0.189),
    ("conditional full D", 0.250, 0.250),
)
C_delta = 0.6063

for label, effective_d, fe_d in cases:
    for Fyb in (106_000, 92_000):
        values = []
        for main_angle, side_angle in angles:
            Fe_m = dfl_dowel_bearing_psi(fe_d, main_angle)
            Fe_s = dfl_dowel_bearing_psi(fe_d, side_angle)
            K_theta = 1 + 0.25 * max(main_angle, side_angle) / 90
            if effective_d < 0.25:
                K_D = 2.2 if effective_d <= 0.17 else 10 * effective_d + 0.5
                R_d = dict.fromkeys(modes, K_D * K_theta)
            else:
                R_d = dict(zip(
                    modes, (4*K_theta, 4*K_theta, 3.6*K_theta,
                            3.2*K_theta, 3.2*K_theta, 3.2*K_theta)
                ))
            result = single_shear(
                main_length_in=3.5, side_length_in=1.5,
                main_bearing_lb_in=Fe_m * effective_d,
                side_bearing_lb_in=Fe_s * effective_d,
                main_yield_moment_lb_in=Fyb * effective_d**3 / 6,
                side_yield_moment_lb_in=Fyb * effective_d**3 / 6,
                gap_in=0, reduction_terms=R_d,
            )
            values.append((result["reference_lateral_lbf"],
                           result["governing_mode"]))
        lo, hi = min(v[0] for v in values), max(v[0] for v in values)
        print(label, Fyb, (round(lo, 3), round(hi, 3)),
              (round(C_delta*lo, 3), round(C_delta*hi, 3)),
              [mode for _, mode in values])
PY
```

## Material basis and limits

NDS-2024 §12.3.6.2 allows `Fyb` to be based on yield strength from ASTM F1575
or tensile yield strength determined under ASTM F606. NDS Commentary Appendix
I.4 describes evaluating tension-test data to estimate `Fyb` and gives the
bolt estimate `Fyb ≈ (Fy + Fu)/2`. The 106 ksi case applies that commentary
estimate to 92 ksi yield and 120 ksi tensile minima for the candidate 1/4-in
SAE J429 Grade 5 screw. It is conditional on those properties and standard
applying to the actual delivered fastener; it is not measured `Fyb` or a
guaranteed lower-bound bending property. The 92 ksi row is analyst sensitivity
only, not a published or NDS-derived `Fyb`.

K.L. Jack lists `25C600HCS5Z` as a 1/4-20 × 6-in Grade 5 screw to SAE J429
and ASME B18.2.1, with UNC Class 2A threads to ASME B1.1. It is a catalog
lead, not a delivered-part or lot-conformance claim. Verify the received
product identity, relevant dimensional/thread properties, and whether the
specified Grade 5 yield/tensile values apply. No blanket external certificate
or bespoke bending-test prerequisite is created by this note.

The conditional `C_delta = 0.6063` is the geometry ratio
`26.95 / (7 × 6.35)`. The 7D denominator is the tension-parallel-to-grain
end-distance screen in NDS-2024 §12.5.1/Table 12.5.1. This ratio is displayed
only if signed action makes the upper-cleat rail row that case; it is not a
standalone NDS capacity factor. No load sign, case, or end-distance adjustment
applicability is established here.

Not checked: actual signed demand, force angle, bolt-group distribution,
group/net-section tear-out, splitting, member net section after all cuts and
bores, cleat internal bending, other member actions, bolt axial/shear
resistance, or complete-joint behavior. These numbers are component
references for joint-development comparisons only; no demand ratio,
failure, or acceptance follows.

Primary sources:

- [ANSI/AWC NDS-2024](https://awc.org/resources/2024-nds/), §§12.3.1,
  12.3.3–12.3.7, 12.5.1, Tables 12.3.3 and 12.5.1, Appendix E, and Appendix I.
- [AWC January 2025 NDS errata](https://web-media.awc.org/wp-content/uploads/2025/03/31134949/2024-NDS-Errata-and-Addenda-03.28.25.pdf),
  p. 4, Table 12.3.1B: `K_D = 10D + 0.5` for
  `0.17 in < D < 0.25 in`; threaded nominal-`D`/root-`Dr` footnote.
- [AWC NDS Commentary, Appendix I.4](https://awc.org/wp-content/uploads/2021/10/AWC_NDS2018-withCommentary_20210113_AWCWebsite_Appendix.pdf),
  for the tension-test estimate method and approximate bolt
  `Fyb = Fy/2 + Fu/2`.
- [ASTM F606/F606M](https://store.astm.org/f0606_f0606m-25a.html) and
  [SAE J429](https://saemobilus.sae.org/standards/j429_201405-mechanical-material-requirements-externally-threaded-fasteners)
  test/specification records.
- [K.L. Jack 25C600HCS5Z](https://www.kljack.com/products/25c600hcs5z/) and
  [ASME B1.1-2024](https://www.asme.org/codes-standards/find-codes-standards/b1-1-unified-inch-screw-threads-un-unr-thread-form)
  thread-standard record.
- [AWC TR12-2026](https://awc.org/wp-content/uploads/2026/06/TR-12_2026_formatted.V3.pdf),
  dowel equations and bending-yield references.

## Provenance

The raw matrix was calculated at repository revision
`c99751dbe8ebadc14d7832eac9346810577f4076`. The relevant method files below
are byte-identical between that revision and the later repository state used
to write this note. The geometry producer was a separate candidate input;
its hash is recorded separately.

| Input | SHA-256 |
| --- | --- |
| Raw copied JSON | `052a6b1b7a130f38dd8d3b73c922503aafac72622c50245d9d8d45f6e35deee7` |
| `fea/dowel_yield.py` | `d6c318e75c1a720d0b91f810a892e8309ef89735f66f48820ee853b753f8fe45` |
| `mini_moonboard/bolted_timber_checks.py` | `a1414547d9eaa3d60e81482b4a2cac2d49e88f31aafa341dca5be9ec8ef4aa13` |
| `mini_moonboard/bolted_wood_wood_yield.py` | `efefbe55279776bc42844cb0aa260bfdd2604f2599dbf9278f6b1754a33c7379` |
| `scripts/wood_joint_wj04_upper_g7_crosscut_probe.py` | `94d2b301450c942f1c7a95f89e3e7ee1ed643ce4db43576c78c1bce04f9302b9` |

The reproducible command above uses the lower-level yield and wood-bearing
helpers to keep nominal-`D` versus root-`Dr` bearing conventions visible.
It adds physically compatible angle samples without editing the copied
matrix. No CAD materialization or native solve was run for this note.
