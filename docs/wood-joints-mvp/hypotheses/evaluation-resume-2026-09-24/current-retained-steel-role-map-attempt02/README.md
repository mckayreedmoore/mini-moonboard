# Retained steel elastic role map, attempt 02

## Corrected contract

Attempt01 is preserved unchanged as an unaccepted contract checkpoint. Its
`default_full_frame_inclusion: false` field and wording that gated scenario
analysis on final rechecks conflated an unselected material option with
omitting required physical connections. Attempt02 corrects that distinction.

All twelve retained frame-bolt connections remain required current-frame
obligations. This map binds their 60 source component roles to a conditional
generic elastic E/nu scenario family, but selects no material scenario. It does
not exclude any physical bolt stack. A conditional scenario study may proceed
before final resistance and fit rechecks are closed; a full-frame native run
still requires defined connection representations, solver mappings, and
bolt/nut engagement assumptions. Final criterion closure still requires the
applicable rechecks.

Each axis has the five modeled roles `head`, `head_washer`, `nut`,
`nut_washer`, and `shaft`. The source `head` and `shaft` rows share one
physical-bolt identity key, while their masses and the other three component
rows remain distinct. No fused FE body or mass allocation is defined.

## Conditional scenario and identity checks

The nine generic isotropic scenarios contain a reference at `E = 200,000 MPa`,
`ν = 0.30`, with derived `G = 76,923.0769 MPa`, plus the existing full grid
`E = 180,000/200,000/220,000 MPa` crossed with `ν = 0.25/0.30/0.35`. These
values are diagnostic input options, not delivered hardware properties or
strengths. The older helper's WJ04 32-body identity is not inherited.

The producer verifies that all twelve manifest axis IDs join exactly five
topology entities each, that all 60 entity IDs are unique, and that the two
recorded receiver members match. All recorded axis vectors are unit length;
source mass centers lie on their corresponding recorded axes within `1e-8 mm`
(observed maximum `8.20e-13 mm`). This is a source-record consistency check,
not physical fit or receiving evidence. The source does not establish
head-to-nut order.

An isotropic fourth-order stiffness tensor was rotated by a proper nontrivial
rotation for each scenario. The maximum component difference normalized to
`E` is `3.93e-16`; this checks isotropic orientation independence only. It
does not assign a material orientation or solver material.

Full-frame manifest readiness remains false and its retained-role material
assignment status is not changed. No solver body, element, DOF, material card,
mass allocation, CAD change, native solve, fit/engagement acceptance,
resistance, or release is produced.

## Reproduction

From the repository root:

```sh
python3 -B docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-retained-steel-role-map-attempt02/produce.py --self-test
python3 -B docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-retained-steel-role-map-attempt02/produce.py --verify
```

The self-test checks 12 axes, 60 roles, all nine scenarios, rotational
invariance, and fail-closed controls for a missing role, duplicate axis,
receiver mismatch, and zero axis direction. `--verify` checks the pinned
source files and reconstructs the JSON and canonical record digest. `--write`
uses exclusive creation in a fresh attempt directory; existing outputs are
never replaced.

## Source pins

| Source | SHA-256 |
| --- | --- |
| Retained role source-to-topology map, attempt03 | `308a329a0b40db454d5b0e27c9ec2eca92d66eec96bfb222df5f7b7185bef4d4` |
| Topology producer | `16645507e1910e038e83b5acc0026b9fb12940db0f194732b355b4ef76a982f9` |
| Current full-frame manifest, attempt04 | `9e682e28c3d4c3c0594863f82c6b74d19dee2700f3856d34e1a26f69082e4f11` |
| Attempt04 manifest README | `7e60cb16f2100fe9da50ccc2617eaeb3a5fba35dd5461d4cce49319bbd15bf9f` |
| Attempt04 manifest producer | `966e4b5918fefe06741ca828a3b4c3f6d353b735a1fc70df6a98a91b4e98b1f4` |
| Full-frame manifest source producer | `0774aa06a560a72411d6fd80da00bd82e81320c7b9191dc36c75641f9f8c9df6` |
| Current material-map status note | `0ad2c85c9fdc6f3cd17a46c57639b4e63c6fd0119d565b45121715f1c1831e6f` |
| Current material scenarios | `dd76354c0fa68a01a336cef22fe1cf854baaaf1ceda22dd11ceb881a274bb3c4` |
| Generic steel scenario definition | `e97f7df51e6553698e1542079d722022cdbbedad83f740ee42d85b56e6b394c3` |
| Steel scenario helper | `0cf45f5194231f61500df14ed580adb9742f6b0c7df659382ea658c7598e8d02` |
| Referenced CalculiX 2.21 manual | `16b6bab5a3f1a40a21fff62379f95c804a58d93758ab2e9a489b18d911dc20c8` |
| Reviewed candidate steel map JSON | `13ed1afcfbc9343207b9e8eb498f8fb3762ec2cdbe0719963f26037cc77027cc` |
| Candidate map README | `a4ca6688d6bece7c4653c421ed52f74f681de10985896d5d4454f89314662222` |
| Candidate map producer | `b625579bc032e32a1100c39f31e50cfea65f74b2137394d500e8055436ca1b26` |
| Preserved attempt01 JSON | `063a03819a4ac0ec62cb72495270cb72cce3d4689ed1a7d1828c2a97f59afb85` |
| Preserved attempt01 README | `96cdbe586406f09f1a6976440657eb6cdf35a983605f67a3060429176d4a111e` |
| Preserved attempt01 producer | `3eded0b72c416c0e9ba9cc7b50526cbe7453eae963b3ce229173d018f90b0f5d` |
