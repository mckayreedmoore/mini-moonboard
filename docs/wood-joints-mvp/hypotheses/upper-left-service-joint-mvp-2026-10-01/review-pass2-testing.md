# Testing review, pass 2

## Medium: receiver-wrench preservation is not asserted

[`test_joint.py:47`](test_joint.py) builds every receiver force and moment as a zero vector, and [`test_joint.py:103`](test_joint.py) checks only that the frozen result still contains 21 boundary rows. The suite would therefore pass if a regression zeroed, sign-flipped, or reassigned the saved receiver wrenches while keeping those rows. Those same-state force and moment resultants are a required input to the remaining complete-joint evaluation, so silently corrupting them would weaken the next analysis while the present HOLD flags stayed unchanged.

Use distinct nonzero force and moment vectors for both receivers in the selector fixture and assert they are returned unchanged. Also check the frozen output's wrench values keyed by case and increment against an independent expected fixture or digest, rather than checking row count alone.
