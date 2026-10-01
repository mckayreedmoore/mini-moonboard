# Independent review: washer eccentricity support screen

Reviewed the frozen files on 2026-10-01. The checker and README hashes
matched the requested freeze:

- `check_eccentric_support.py`: `97b6426cdc84364bfe8967d491906189b153d8805bbd53290f08dc5f730ce035`
- `README.md`: `73cf3237091ce4be70f3a34656e2f4f1701cdc127ee99426fd7166f2de055bbb`

From the repository root, both commands passed:

```sh
uv run --no-sync python docs/wood-joints-mvp/hypotheses/corner-washer-eccentric-support-2026-10-01/check_eccentric_support.py --self-test
uv run --no-sync python docs/wood-joints-mvp/hypotheses/corner-washer-eccentric-support-2026-10-01/check_eccentric_support.py --check
```

The self-test exercises disjoint, contained, concentric, partial, and tangent
circle cases; compares the production STEP measurement with a known formula
case; checks inward and outward swept envelopes; and confirms rejection of a
neighboring bore, outward boss, failed envelope flags, missing comparisons,
nonfinite error, and error beyond tolerance. The previous fail-open behavior is
fixed: `build_report()` calls the gate before returning, and failed envelope
or area-oracle checks produce a nonzero exit. Its reported thresholds are a
dimensionless swept-fraction tolerance of `1e-7` and a direct area tolerance
of `2e-5 mm²`.

The exact disk-intersection formula and washer-annulus subtraction are
consistent with independent calculations. For plain 25NWUS minimum OD
(`0.727 in`), I independently calculated the following supported areas from
the bore-only formula:

| Washer ID | Bolt held on modeled bore axis | Combined aligned clearances |
| --- | ---: | ---: |
| `0.307 in` | 216.195105 mm² | 211.888448 mm² |
| `0.327 in` | 210.250405 mm² | 206.013152 mm² |

For the mixed-source F436 minimum OD (`0.729 in`) with those same plain-washer
ID bounds, the corresponding supported areas are 217.670637/211.725937 mm²
with the bolt held, and 213.363980/207.488684 mm² with combined aligned
clearances. These are geometric sensitivity values; the packet labels the
F436-OD/plain-ID combinations as mixed-source and does not transfer material
properties or resistance.

The full BREP envelope check covers radial distances from the modeled bore
radius, `3.75 mm`, to the largest declared outer radius plus combined offset,
`11.0652 mm`, at all twelve outer seats and depths `0.01`, `0.05`, and
`0.1 mm`. All-direction inward containment is true within tolerance; the
minimum fraction was `0.9999999999994897` and the largest reported missing
volume was about `1.04e-11 mm³`. Outward overlap was zero. Because the complete
annulus over that radial interval is checked against each BREP, this is the
continuous in-plane envelope proof for the declared offsets and OD bounds;
the 0°, 45°, and 90° BREP comparisons remain diagnostic samples. The direct
sampled area differences from the analytic formula were about `1e-9 mm²`.

The replay pins the prior checker and README, the hardware source, the source
JSONs, implementation, and CAD dimensions. It rehashes each imported STEP
against the model binding and bundle manifest and validates the imported
solid. A small reporting limitation remains: the eccentric packet's output
hash map reports the bundle-manifest digest but does not emit the four STEP
digests directly, even though they are checked during replay; those digests
remain available from the pinned base packet.

The body diameter is the recorded nominal `6.35 mm` smooth-body scenario, not
a minimum delivered shank. The bore is `7.5 mm` in the analytical model, not
an inspected hole. The combined offset is the same-direction sum of those
modeled circular clearances. No delivered dimensional bounds, bolt tilt,
seat drift, or fabrication tolerances are included. The reported unsupported
area does not determine contact pressure or resistance and is not a failure or
adopted-criterion result. No material strength, load-transfer acceptance,
joint acceptance, six-case envelope, or physical build is established. The
frozen bundle also lacks a semantic cut inventory, so absent cuts cannot be
verified by this geometry replay.
