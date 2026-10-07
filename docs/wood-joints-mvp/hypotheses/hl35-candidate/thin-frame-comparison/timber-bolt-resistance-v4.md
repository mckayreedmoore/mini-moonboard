# Reviewed thin-frame timber and bolt component evidence

[The issued numerical packet](timber-bolt-resistance-v4.json) is bound to the
reviewed `compact-floor-flush-thin-bolted-development` V4 layout
(`8174841bf64914570397ee6d960c5602f74097e2e412e5910502811bc5b9405c`)
and the shared [native geometry cache](native-geometry-v4.json). Its SHA-256 is
`5e78ac49a2db2050caf7ee7d2002d0ebf4f9a92496e857a0e2d652629bd0d848`.
All candidate, complete-joint, capacity and release flags are false.

The packet records all 70 physical shafts, 82 separate timber bearing
intervals, 72 flange attachments and 140 washer ends. The four rear frame
shafts have runner bearing from 0–38.1 mm and leg bearing from 38.1–88.9 mm:
their wood-support union is continuous. The leg's actual bearing length is
50.8 mm. The rear recess is not restored into that bearing length. Geometry
continuity does not verify delivered contact between members.

The boundary query restores only the matching, fully circumferential bore
wall intervals, retaining all other cuts. Partial cylindrical walls are
refused. Five depth probes per interval find the first material boundary and
retain square/oblique face metadata. The unfilled finished bodies supply
1,050 exact zero-thickness section samples across 20 members. These samples
do not prove a continuous minimum or supply a section-wrench stress check.
At planes having the full raw cross section, sampled minimum retained-area
fractions range from 0.525974 for the recessed legs to 0.920455 for the
runners. No wood fracture or splitting resistance follows from area alone.

The declared DF-L No. 2 basis uses NDS-2024 Supplement Table 4A dimension
lumber for both nominal 2×6 and 4×6 stock: G=0.50, E=1,600,000 psi,
Ft=575 psi, Fv=180 psi and Fc⊥=625 psi. Raw references use CD=CM=Ct=1
and omit size-factor increases. Actual stock and moisture were not inspected.

| Conditional component scenario | Unadjusted reference range |
| --- | ---: |
| 72 isolated steel-to-wood planes, body diameter, 0°/45°/90° | 1.113–3.174 kN |
| Same planes, explicit 0.8D root sensitivity | 0.979–2.123 kN |
| 12 retained two-member shafts, actual separate bearing/grain geometry | 1.058–2.581 kN |
| Same retained shafts, explicit 0.8D root sensitivity | 0.840–1.689 kN |

Each steel-to-wood scenario evaluates all six single-shear modes. The retained
curves also evaluate all six modes, with one opposed lateral force direction
and both actual grain directions. Generic Fyb=45,000 psi is the published
[AWC TR12 table basis](https://web-media.awc.org/wp-content/uploads/2021/12/17210714/AWC-TR12-1510.pdf),
not an authenticated delivered bolt property. Fe=49,500 psi is a conditional
AISC-bearing parameter derived as 2.4Fu/1.6 under Fu≥Fy=33,000 psi and the
[Eaton material hypothesis](https://www.eaton.com/us/en-us/catalog/support-systems/strut-fittings-and-accessories.html).
Product conformance, the Fu inference and metal-method applicability are
separate conditions. The 0.8D root is an explicit sensitivity, not a measured
or standardized minimum. Full-body use requires the NDS thread-exposure rule
in every bearing member. No opposed-side values are added into a shaft rating.

The 68 direct-wood washer ends have ideal full-contact annulus references of
1.766–3.467 kN. The 72 washer-on-steel ends receive no washer-on-wood annulus
value. Actual washer spreading, head/nut/thread strength, bolt tension,
plate-to-wood contact and local fracture remain separate.

The signed action API requires immutable `state_id`, `case_id`, shaft,
flange/member identity and the exact flange entry datum. It preserves both
force vectors and free moments. A shared shaft enters the maintained
symmetric four-mode method only with equal lateral vectors and zero free
attachment couples. Unequal shared-side actions require a common-shaft
response method. No fresh compatible demands were supplied in this unit
packet. Signed finished end/edge classification, connected group action,
critical row/group tear-out, splitting and complete axial interfaces remain
unevaluated; the packet reports no reserve for them.

The source-bound producer is
[thin_bolted_timber_resistance.py](../../../../../scripts/thin_bolted_timber_resistance.py).
Its 15 known-answer and fail-closed tests pass. The issued 1.30 MB packet
retains the complete shaft/member topology, controlling geometry rows and
all numerical mode curves. Verbose probes and sections remain in ignored
`fea/generated/thin-bolted-v4-geometry/`, with hashes and an exact prior
producer snapshot. Authentication verified every recorded nonproducer
source and byte-identical geometry functions; the 1,050 queries were reused.
These caches remain active inputs for fresh demand comparisons.

```sh
UV_CACHE_DIR=/tmp/thin-timber-uv-cache uv run pytest -q tests/test_thin_bolted_timber_resistance.py
UV_CACHE_DIR=/tmp/thin-timber-uv-cache uv run python -m scripts.thin_bolted_timber_resistance \
  --reuse-geometry fea/generated/thin-bolted-v4-geometry/timber-geometry-query-full-v4.json \
  --geometry-producer fea/generated/thin-bolted-v4-geometry/timber-geometry-query-producer.py \
  --detail-out fea/generated/thin-bolted-v4-geometry/NEW-full.json \
  --out fea/generated/thin-bolted-v4-geometry/NEW-compact.json
```

Use new output paths; the producer refuses to overwrite frozen evidence.
