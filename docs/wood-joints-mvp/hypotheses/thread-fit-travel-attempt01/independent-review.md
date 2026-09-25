# Independent review: conditional 1/4-20 thread-fit travel comparator

**Reviewed:** 2026-09-25. **Result:** the ideal-profile derivation and its
non-claims are sound for the stated fixed-relative-rotation comparator. The
values are not a selected WJ24 pair, measured installed gap, or axial-travel
bound for an unconstrained nut.

## Reviewed input pins

- [Current method note](../../current-thread-fit-travel.md): SHA-256
  `4046318d1fac274bc3a2bb654921d3eaa4bce9c33e2cc2c391b8b83f4ac8d50d`.
- [Attempt 01 README](README.md):
  `96f40a89ce49fa91c414f29c845feb9f1ee8d5f6129bf4b8f8a342eea893d4fb`.
- [Attempt 01 calculation](calculation.json):
  `206ff1dae7d83b739d5af909e27309b2d8e2f1dda399c190f07a4def9898c43b`.
- [Current ordinary-hardware basis](../../current-ordinary-hardware-basis.md):
  `72ffabef1e449234622f4682eaefcde787abc1b56fbe8814b1e843d1581d1ecc`.

## Numerical and geometric check

The linked [NBS Handbook H28 (1969), Part I](https://nvlpubs.nist.gov/nistpubs/Legacy/hb/nbshandbook28-1969p1.pdf)
is a primary historical source for the stated 1/4-20 UNC limits: external
2A pitch diameter 0.2127–0.2164 in and internal 2B 0.2175–0.2224 in. Its §9
relation is `δE = δp cot(α)`; for a 60° included thread angle,
`α = 30°` and `cot(α) = 1.7321`. Under the note's ideal, matched-profile
assumption, the pitch-diameter clearance is diametral, so inverting the
relation gives the full flank-to-flank axial reversal band
`b = (D2 − d2)/1.7321`. No additional factor of two is missing: the
diametral clearance already includes the radial spacing on both sides.

Recalculation gives `0.0011–0.0097 in` diametral clearance and
`0.00063507–0.00560014 in`, or `0.0161307–0.1422435 mm`, axial reversal.
The conversion to the reported rounded range is correct. With relative
rotation held fixed, an arbitrary unpreloaded starting phase can move zero
to the full reversal band before the opposite flank contacts; a centered
ideal position gives half the band to either side. The single-start 20-TPI
kinematic relation is also correct: 1.27 mm per relative revolution. If
rotation is free, class fit does not bound multi-turn axial travel without
actual restraint and end-stop/thread-end geometry.

## Applicability limits and edition status

The note correctly treats H28 as a historical reference rather than current
procurement acceptance. ASME's [B1.1-2024 standard record](https://www.asme.org/codes-standards/find-codes-standards/b1-1-unified-inch-screw-threads-un-unr-thread-form)
is the current-edition source, but the public preview does not expose the
numeric tables. The note appropriately requires current-table confirmation
before acceptance use and does not infer that H28's numerical limits remain
the current limits.

Its full-form overlap condition is essential: standard nut thickness alone
does not show that one complete turn survives nut entry/exit chamfers and
bolt thread runout. The note keeps the initial flank/phase, final thread
profiles and coatings, actual pair, and rotational restraint unresolved. It
does not turn the ideal comparator into installed WJ24 slack, stiffness,
strength, friction, self-locking, or capacity. I found no material
correction needed within those bounds.
