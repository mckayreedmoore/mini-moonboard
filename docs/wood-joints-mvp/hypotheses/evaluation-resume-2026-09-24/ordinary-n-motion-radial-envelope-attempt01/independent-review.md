# Independent review

The independent reviewer reproduced `produce.py --verify` byte for byte and
checked the source/helper pins, all 35 contact-pair identities, exact radial
face counts and the C3D10 face mapping. The 16 addressed pairs are exactly
eight shaft/wood pairs and eight shaft/washer pairs. No correction was found.

The reviewer independently checked the quadratic Bernstein control conversion,
the four parameter subdomains, the nonnegative-basis hull argument, the
projection lower bound, norm upper bound and translation-norm subtraction.
The sampled polynomial reconstruction error is 1.78e-15. The assumed midpoint
hardware-stack motion gives 0.25 mm shaft/receiver offsets under the recorded
±0.5 mm port translations; that is an assumption of this geometric witness,
not a solved hardware trajectory.

The original whole-face minimum −0.4169030987 mm is correctly retained as an
inconclusive bound. One exact parameter subdivision gives a smallest computed
wood-pair separation of 0.0931497349 mm at `WJCP_024`; subtracting the numerical
reserve leaves 0.0931487349 mm. The washer minimum after reserve is
0.6725849896 mm. No mesh or model geometry was modified.

The review confirms the stated limited conclusion. It does not establish
trimmed-seat compatibility, a solver contact state, exact zero force,
equilibrium, onset, resistance, joint acceptance or release.

Reviewed files:

- [produce.py](produce.py): `6495d924e1581ef57b8fabc47d654073959462639f4e7c9c9216f589e47058cd`
- [radial-envelope.json](radial-envelope.json): `e459e979e33d9deb85ae5064fa27b2d2a78280ec87986bc40fc0ab4335a3ae3f`
