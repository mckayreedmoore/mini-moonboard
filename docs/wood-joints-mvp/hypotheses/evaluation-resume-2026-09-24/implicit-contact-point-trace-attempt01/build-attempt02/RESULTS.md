# Build attempt 02

Compilation succeeded, but independent code review found a diagnostic varargs defect: the integer `kscale` was passed to a `%.17e` conversion without a cast. This executable is not qualified and was not used for a native solver run. Its build and binary remain preserved. Attempt 03 adds an explicit double cast to that output argument, preserving the record schema and all solver calculations.
