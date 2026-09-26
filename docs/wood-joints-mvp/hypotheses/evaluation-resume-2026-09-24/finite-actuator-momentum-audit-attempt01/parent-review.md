# Parent review: cleat interval omission

The parent executed audit.py SHA-256
`f2efc89d444e37b66e65e911f3c079a1240fd01e0f28954c5ed17861ff861a33`
in the pinned Gmsh image with one CPU and a 4 GiB limit. The run completed.
Report SHA-256 is
`3ccf011ecd8de1d9aea1913820156df5d1b9c65d6d247cd20d9b12e4c80cea49`.

All four global accepted-to-accepted linear momentum residuals are within
the report's printed-output bounds under both distinct mass operators.
However, every cleat interval is null. This report does not deliver its
stated three-interval cleat balance.

The declared exact contact times were passed through a printed-number
matching function. Short strings such as 0.001 and 0.002 acquire coarse
half-last-digit tolerances, allowing multiple accepted states to match.
Selecting the first match yields required indices [0, 0, 2, 2], so no
adjacent interval has both endpoints selected. This is an audit-selection
bug, not unavailable source contact evidence or a mechanics failure.

Preserve this attempt. The corrected audit must match the exact declared
Decimal times uniquely, select indices [0, 1, 2, 3], and assert that exactly
three cleat intervals are evaluated before claiming that coverage.
