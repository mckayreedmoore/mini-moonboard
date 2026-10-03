# Corner net-section normal-stress reference screen

**Result:** all six case/member summaries are source-bound to the existing 252
one-sided affine normal-traction records. Both screened members' section
normals align with their proposed longitudinal grain. This permits a
conditional parallel-grain reference comparison without rotating the
existing stresses.

For each case and member, the table reports the largest positive and most
negative nominal affine normal stress across the existing load increments,
section stations, cut sides, and section outer corners. Tension is compared
with conditional DF-L No. 2 `Ft∥ = 575 psi`; compression magnitude is compared
with `Fc∥ = 1,350 psi`. Those are unadjusted Table 4A base-row references,
converted here with `1 psi = 0.006894757293168361 MPa`. Ratios are
proxy-to-reference arithmetic only.

| Case | Member | Peak tension proxy, MPa / `Ft∥` reference | Ratio | Peak compression proxy, MPa / `Fc∥` reference | Ratio |
| --- | --- | ---: | ---: | ---: | ---: |
| A12 rear | Spine | +0.427677 / 3.964485 | 0.107877 | 0.302229 / 9.307922 | 0.032470 |
| A12 rear | Inner-frame block | +0.041445 / 3.964485 | 0.010454 | 0.041176 / 9.307922 | 0.004424 |
| A1 rear | Spine | +0.155821 / 3.964485 | 0.039304 | 0.214733 / 9.307922 | 0.023070 |
| A1 rear | Inner-frame block | +0.031476 / 3.964485 | 0.007939 | 0.040902 / 9.307922 | 0.004394 |
| K12 rear | Spine | +0.122567 / 3.964485 | 0.030916 | 0.146661 / 9.307922 | 0.015757 |
| K12 rear | Inner-frame block | +0.010926 / 3.964485 | 0.002756 | 0.018069 / 9.307922 | 0.001941 |

The governing spine proxy in both signs is A12 rear: tension at
`knee_outer_left_side_1`, `just_below`, load factor 1.0; compression at the
same station and cut side. For the block, A12 rear also governs both signs at
`knee_outer_left_side_1`, `just_below`, load factor 1.0. Exact row keys and
unrounded values are in [`net-section-material-reference.json`](net-section-material-reference.json).

## Applicability and conditional scenario

The three pinned case models define both section bases as `u=+X`, `v=+Y`,
with member axis `+Z`. Their section-plane normal `u×v` is therefore `+Z`.
The current material map proposes `+Z` longitudinal grain for both
`knee_outer_left_spine` and `knee_outer_left_inner_frame_block`; the absolute
grain/normal dot product is 1.0 for each. These are proposed axes, not
measurements of stock grain.

The selected reference arithmetic uses the conditional DF-L No. 2 base
properties under the documented dry-service, normal-temperature,
non-incised, normal-load-duration scenario. It applies `CF=1` and no `CD` or
other adjusted-capacity credit. For the standard nominal 2×6 spine, this
deliberately omits the listed Table 4A `CF` values of 1.30 for `Ft∥` and 1.10
for `Fc∥`; the resulting ratios remain comparisons to the named unadjusted
references, not adjusted NDS checks. The inner-frame block is a cross-section
rip with no supported Table 4A size class or code `CF`. Its `CFstudy=1.0` is
the explicit hypothetical final-section arithmetic scenario only; it does
not transfer the original stock's grade or design values.

The proxy producer assumes a common affine strain field over the existing
rectangular-minus-bore sections. The inner block's BG003 center cuts have
disconnected ligaments, so common strain across them has not been established.
The extrema are nominal section proxies, not local hole-wall stress or proof
of force transfer. This screen does not establish stock species/grade, final
dimensions, local net-section resistance, a design-value basis for the ripped
block, splitting or stability resistance, adjustment factors under actual
conditions, interaction, or complete-joint acceptance. No physical failure
or pass is inferred from these ratios.

## Source pins and replay

The producer pins the existing `normal-traction.json` and its converter, the
three source case models that establish section axes, current material inputs
and narrative, and the local Table 4A / PS 20-25 source files. The complete
SHA-256 list is embedded in the result. The primary input pins include:

| Input | SHA-256 |
| --- | --- |
| Existing normal-traction output | `4ac5094c733f4497c69f9890858581c1a283cb2782c1922f0a149185df66c386` |
| Existing normal-traction converter | `885d883f67e6be64c68790ace19a33c1e30710ab5b225e1a1666397b750c63f0` |
| Current material inputs | `0f33ad8fd517673a4ebbed36c4a30c1cfe07e0d8163165bdc804af91d958fc5a` |
| Current materials note | `943e5ecb26a5bb9e49e55e4c510bbbf697b08a6b9415c26bbcb41c48db70a2d6` |
| AWC 2024 NDS Supplement Chapter 4 PDF | `1f65975633f111c308944c470b6cc10e9207b6c45e8a0804b8bdec3378bbc71b` |
| NIST PS 20-25 PDF | `8868066272130bf7a6621b7fda6f9539bf2e26e57975f2c6c00489b6613f51ca` |

From the repository root, replay the source proxy and this screen read-only:

```sh
python3 docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-corner-net-section-normal-traction-attempt01/convert.py --verify
python3 docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-corner-net-section-material-reference-attempt01/produce.py --verify
```

`produce.py --verify` checks exact source hashes, confirms the proposed grain
and section-normal alignment in all three models, recomputes the six extrema
and ratios from the existing rows, and compares the replay byte-for-byte with
the saved output. It performs no solve or file write.
