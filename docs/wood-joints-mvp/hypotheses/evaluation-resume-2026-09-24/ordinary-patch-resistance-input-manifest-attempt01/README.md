# Ordinary-patch conditional resistance-input manifest

**Status:** source-pinned, pre-demand scenario inputs only. This fresh attempt
binds the owner-reviewed `led-clearance-2x6-runner-seated-blocks-v1` revision
to its ordinary bottom-center-right patch: three full timber members, four
physical bolts, three separate wood interfaces, and eight washer seats.
`manifest.json` records the exact member, bolt, and seat identities and pins
the geometry, prior reviews, material and hardware records, and method basis.

The bolt input is a hypothetical 1/4-20 SAE J429 Grade 5 cap screw with
project-specified minima `Fy = 92 ksi`, `Fu = 120 ksi`, and `Fp = 85 ksi`,
plus nominal tensile stress area `At = 0.0318 in²`. These values are conditional
inputs for a specified scenario. No product or lot is selected, received, or
verified. The area is not a measured thread-root or shank section. This
manifest calculates no steel resistance or interaction.

The independently reviewed washer-to-wood preflight is carried forward only as
a conditional component-reference screen, without recalculation:
920.57–1,019.16 N per seat under conditional dry DF-L No. 2 `Fc⊥ = 625 psi`
and a 1/4-in Type A Wide washer dimensional envelope. Its assumptions are
uniform annular compression, full support on sound wood, no preload, and no
bearing-area increase. The reference stays per seat; the eight values are not
summed. Delivered stock, washer identity, active pressure, and washer steel
response remain unknown.

The NDS `Fyb` field stays unresolved. NDS-2024 §12.3.6.2 identifies ASTM F1575
bending-yield testing or ASTM F606 tensile-yield testing as the basis; a
tensile result still needs an evaluated derivation into `Fyb`. Grade 5 `Fy`
does not supply that basis. No `Fyb` value is assigned, and the Commentary
`(Fy + Fu) / 2` estimate is excluded from this scenario. Thread-root geometry,
member-specific thread-bearing lengths, the NDS diameter selection, nut
engagement, washer steel method, and a combined-action method remain open.

The current six-case source file records applied force/wrench inputs only.
It supplies no current frame reactions, patch actions, per-bolt demand, or
load shares. Under the Step 5 definition in `next-mvp-plan.md`, resistance
criteria remain unresolved until supported methods are applied to fresh
current demands. The input preparations for `steel_direct` and
`washer_bearing` do not resolve either criterion. No criterion result is
calculated; demand, criterion, acceptance, and release flags remain false.
No criteria, plan, ledger, or release record is edited by this attempt.

Current official method records checked on 2026-09-27:

- [ANSI/AWC NDS-2024](https://awc.org/resources/2024-nds/), including Chapter 12
  §§12.3.6.2 and 12.3.7.1–12.3.7.2. The pinned boundary note links the official
  Chapter 12 PDF and records its SHA-256.
- [ASTM F1575/F1575M-24](https://store.astm.org/f1575_f1575m-24.html), active
  test-method record.
- [ASTM F606/F606M-26a](https://store.astm.org/f0606_f0606m-26a.html), active
  test-method record. The edition choice for a future NDS basis remains open.
- The official AWC 2024 NDS errata record consulted with this basis is linked
  in `manifest.json`.

From this attempt directory, run the read-only source and identity verifier:

```text
python3 verify.py --verify
```

The verifier hashes pinned sources and checks the candidate, patch, and false
status fields. It writes no files and runs no CAD or solver code.
