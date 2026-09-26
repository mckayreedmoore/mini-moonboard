# Independent review

The bounded contact-history audit is internally consistent with its pinned
snapshot and pair definitions. I verified the snapshot manifest SHA-256
`001cefdb37a52bdf6bc6d1d590310c93d91d7f5b2f7cf0a35ad2e10c097e0d8a`,
input-freeze SHA-256
`f054d6b911fb0d9c9b0a183fa007d16d8a34a422904fd5cbcf73634e87797e66`,
DAT SHA-256
`5b9ef4ed407c11008c0d2f31dc92037a08564a41859825c0a54ea587f71fa3e4`,
and STA SHA-256
`f122d34446295f3b6d0a0b3d70605b7c05163829fcf12d56da988de8cd921a30`.
The final audit report SHA-256 is
`b50ab4608ce3346fbe3f2399794fc98e7ef18a6fe8a3d62ad1e1a075960ec1e4`;
its producer is pinned at
`37114577aac614952db215b5aa7c361df2b7e16b01133736d480db1a128c87ae`,
and it loads the strict terminal parser and first-knot helper pinned at
`d97c57f64d5d8a37b5617e45c353334be37ca3bbcc43f64039425bdd6e968b14` and
`8d32aed77f1bffdec3101747c1e2c40eb9cc5e3fb8707ddee89e24d1a458c40c`.

I independently checked the exact frozen every-increment input deck
`pilot.inp` (SHA-256
`a9f891c92fed7eaa7e3b78f0656c5829d330a28a3df450ea7128b9ea52eb49c4`)
against its input-freeze entry and the pinned contact manifest. Deck
validation found 35 pair-specific `CONTACT PRINT` requests in manifest order,
each requesting `CF,CFN,CFS`, plus one global `CDIS,CSTR,CELS,CNUM` request.
The parser assigns the three output blocks to each pair by sequence slot and
requires the slave and master surface IDs to encode the same expected WJCP
index. All 2,095 captured pair headers passed both checks. `CFN` is retained as
a duplicate normal-force report rather than added to `CF`; `CFS` remains
separate.

There are 20 accepted states, from 0.001 through 0.020 s. At each of the first
19 states, WJCP_020, _022, _024, and _026 have complete exact-zero CF vectors
and zero reported area. At 0.020 s, all four have complete nonzero CF vectors
and positive reported areas. Each is mapped to the cleat as master
(`W00_BOTTOM_CENTER_RIGHT_CLEAT`) and its corresponding bolt-head-plus-shaft
union as slave:

| Pair | Reported area (mm²) | CF (N) |
| --- | ---: | --- |
| WJCP_020 | 2.395896 | (-1.538434, -8.615487, 7.227133) |
| WJCP_022 | 6.103547 | (-0.4641958, -7.852277, 6.589487) |
| WJCP_024 | 3.977105 | (0.01732653, -11.13889, 9.65674) |
| WJCP_026 | 2.795686 | (0.01363635, -11.31264, 9.925294) |

The first 19 states have all 35 pair triplets. At 0.020 s, 33 triplets are
complete, WJCP_034 is partial, and WJCP_035 is missing. WJCP_034's printed
zero CF vector is not a complete CF record: its area is unavailable, and CFN
and CFS are missing. WJCP_035 has no CF, CFN, or CFS record. Both remain
unknown rather than zero. Global CDIS/CNUM row counts are complete at all 20
states; that does not fill the missing pair reports.

This is a contact-output observation through the last captured accepted state,
not proof of complete physical seating, strength, reaction balance, or joint
acceptance. The capture was non-atomic and the execution record was still
`running`; no inference follows after 0.020 s or between accepted states. No
live outputs, native solver, or CAD were accessed for this review. The snapshot
contains FRD, but no CEL or FRD fields were used; CEL was absent and FRD was
not read or hashed.
