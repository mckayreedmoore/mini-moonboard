# First assembled-frame input attempt

The complete source-case assembly passed its input checks, was frozen and
independently reviewed. One serialized native invocation then exited 201 in
0.69 seconds while parsing `*ORIENTATION`; no displacement solution exists.
The original [deck](cycle-00/model.inp), [log](cycle-00/native.stdout),
[execution](cycle-00/execution.json) and [input review](cycle-00/review.json)
remain unchanged. This is neither a convergence result nor structural failure.

The material-axis writer used 17 significant digits. Forty-two orientation
fields exceeded 20 characters. CalculiX reads the first 20 characters as a
real number; an exponent clipped at that boundary can be treated as a
distribution name instead. The same behavior is visible in the
[upstream parser](https://github.com/Dhondtguido/CalculiX/blob/master/src/orientations.f)
and was confirmed by reading `orientations.f` directly from our pinned 2.23
image. The exact source archive in that image has SHA-256
`9c88385c10fb04f5dc6c4e98027a51bebdd8aee3920e05190d6c1dd08357d6e7`.
An [earlier report of the same error](https://calculix.discourse.group/t/errors-with-orientation/2288)
helped locate the issue; the pinned source supplied the version-specific check.

The forward fix writes orientation values with 13 significant digits and
rejects overlong numeric data before a new freeze. Checking the entire
corrected deck found no other overlong numeric fields. Maximum change to a
serialized orientation component is 4.92e-14; the recorded material vectors,
geometry, loads and mechanical assumptions remain unchanged. Attempt02 is
rebuilt and frozen separately. The consumed run ID is not reused.

This first case is A12 rear, no accessory mass, zero bolt clearance and an
explicitly nonqualifying Hillman axial/lateral stiffness ratio of one. Its
initially active normal and tension branches still require solved sign and
equilibrium checks. No current joint or MVP criterion is accepted here.
