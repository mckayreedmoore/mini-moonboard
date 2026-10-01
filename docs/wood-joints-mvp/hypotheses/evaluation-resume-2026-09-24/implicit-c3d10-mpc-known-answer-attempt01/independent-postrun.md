# Independent post-run review

I independently checked the frozen packet and the two captured native runs on
2026-09-27. This review is read-only with respect to frozen inputs and native
outputs; it performed no solver run. The input-freeze SHA-256 is
`b9e74647a23fbf5e458c0d2873eb491a0428c5bbae341ce72ff25f399db8036c`.

All 11 local frozen-file hashes and all four external dependency hashes match
`input-freeze.json`. Both case-execution records match their recorded hashes,
and all 18 per-case output-file hashes match their captured bytes. The aggregate
execution record hashes to
`918d43a5a6da7591f2b724004596ed7393eec11846725cd4d90359b8b8afbcec`. The direct
and mapped case-execution record hashes are
`2bc9a8125fb3156f51f376ca6390235123c0971a855216557d1a2a9f815da313` and
`ef05de62236aa8c2935b6983241b54464176b58f7ededcd672bf82c64f1f361b`,
respectively. The output manifests bind the direct and mapped DAT files to
`cf7dc4fbf6e88cbddd7b3799c32ed35d7962a650a9307046673062330549b5b6` and
`92ca9c9faae247b1989394ef68925a6cede787713e89d06c65829908c17b309a`, and the
FRD files to `d36ba150d42408c3050ad512c0ac0e706ea696d7f994448725de64c6b13c80ad`
and `1b1380b8bbf8c62d0bfa46e18ca435bd98f685b2f418fe281fb7110ce58ec90c`.

Both records identify the same pinned image
`sha256:31336f517557f5dd5f97d85b1e6e15947fd1c10b44edc1364dbba4c1a5ab6c38`
and binary SHA-256
`c6882d262b44525a563250673420dff1506c41b95e6d82d50392f9af26111863`. Docker
inspection confirms both containers exited zero without OOM, used network
`none`, one CPU, 1 GiB memory and 1 GiB memory-plus-swap. The direct run started
at `21:33:27.026599859Z` and finished at `21:33:27.810299495Z`; the mapped run
started later, at `21:33:27.969788828Z`, and finished at `21:33:28.756975530Z`,
so the cases did not overlap. Both captured stdout contains `Job finished`,
stderr is empty, and each native output total is below the frozen 16 MiB cap.
The records specify one OpenMP thread, one solver process and a 60-second
per-case limit; each observed run completed in about one second.

I parsed the raw DAT, FRD and STA captures. Each `.sta` has exactly 100 accepted
rows, step 1, attempt 1, two iterations per row, from 0.001 to 0.100 seconds.
Each DAT has 100 `OBSERVE` displacement states and 100 velocity states. Direct
output covers physical nodes 1–10; mapped output also reports free controller
node 11. Each case has 100 records for each of `ELSE`, `ELKE`, `EMAS`, and
`EVOL`. Each FRD has 100 `DISP` and 100 `VELO` blocks with step/increment
identities 1/1 through 1/100 and all 10 connected physical nodes.

Both cases match the frozen Newmark uniform-translation oracle. At the first
state, `t=0.001 s`, the physical translation is `U1=2.5e-10 mm` and
`V1=5e-7 mm/s`; at `t=0.1 s`, it is `U1=0.000166675 mm` and
`V1=0.005 mm/s`. The terminal kinetic energy is `1.25e-5 N·mm`; mass is 1 tonne,
volume is 1/6 mm³, and elastic energy is numerically zero. The independently
computed maximum DAT displacement error is `5.0000000044e-11 mm`; the maximum
DAT velocity error is `8.6736173799e-19 mm/s`. FRD displacement and velocity
records track DAT within the frozen output precision limits. Physical-node DAT
U/V values are exactly identical between direct and mapped runs at every common
state. Mapped controller U/V also follow the oracle; evaluating the printed
values of `U1(1)+U1(2)+U1(3)+U1(4)-4*q11` with decimal arithmetic gives zero at
all 100 states, within each row's printed-value rounding bound.

The frozen verifier reports `PASS_IMPLICIT_C3D10_MPC_KNOWN_ANSWER`, consistent
with these raw checks. This result supports only the tested zero-initial-state,
uniform-translation load and this single free-average-coordinate mapping on one
straight C3D10. It does not establish arbitrary quadratic mass modes, other
physical pivots, contact behavior, joint resistance, work-energy acceptance,
structural acceptance, or release. The packet's acknowledged four-point
C3D10 mass underintegration remains a limitation outside this exercised
uniform mode.
