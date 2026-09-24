# WJ-05 center post ±190 mm geometry diagnostic

This isolated diagnostic moves the two center posts, their lower cleats, and eight lower bolt axes 10 mm outward, from post centers at ±180 mm to ±190 mm. Upper cleats and axes, active backers, the fixed 66 panel/kicker axes, and the 12 starting frame-bolt arrangements remain fixed. The variant does not inherit capacity or acceptance from its source trial.

The source-bound report is [wj05-center-post-x190.json](wj05-center-post-x190.json), trial `wj05-center-node-posts-x190-outward-v1`. Its SHA-256 is `e99742f40d9ddbd14fd4de697008ca8c9e7689db6d6de5b3b8abc4d0502e5a58`. It records `nominal_geometry_clear_diagnostic`: member bodies, proposed bores, installed hardware, receiver volumes, washer seats, contact-face coincidence, wire clearance, and preferred modeled tool-route envelopes pass their geometric checks. Both lower-cleat/header seats meet at Z=238.9 mm, with gross projected contact area 7903.21 mm² per side. Areas are not net of bores.

The right upper-cleat wire clearance is 2.303793 mm to `wire_072_F1_G1`; the left side has a proven lower bound of 9.25 mm. Both exceed the diagnostic 2.0 mm screen. The rejected ratchet stroke sector still has diagnostic backer intersections on each side; only the selected left −5° and right +5° sectors gate the preferred-route result. Catalog tool envelopes do not establish physical tool access or fit.

The shift increases post support-center spacing from 360 to 380 mm, increases lower header bolt-group center spacing from 488 to 508 mm, and reduces upper-cleat/post projected overlap from 17 to 7 mm. These changes need fresh mechanics and complete-joint review. No strength is assigned, and no complete load path is accepted.

The materializer starts from raw source-derived timber. Some retained source openings may therefore be absent, making timber collision results conservative pending machining integration. The report also states that service/tool tolerance and contact areas net of bores are not established.

The initial pre-fix diagnostic is preserved byte-for-byte as [wj05-center-post-x190-contact-face-pre-fix.json](wj05-center-post-x190-contact-face-pre-fix.json), SHA-256 `d27bb1518c7e72f3490be0d4bb2213272a17f5228965cd132cd7bfdb5f69bcea`. It used producer SHA-256 `6361bd54f3ca64b71de4197f500701d0d59067b4943ba5ae9f0217834ee79aec` (commit `8bbe1b4a`). Its only failing summary gate came from comparing the lower cleat minimum-Z face with the header maximum-Z face. The corrected producer compares the actual mating faces, lower cleat maximum-Z and header minimum-Z at 238.9 mm; geometry and all other checks were unchanged.

The corrected producer SHA-256 is `b97723f66caabb200f1504011196543ceb1e4f7f2587c09be0300cd72f43f9d8`; its focused test SHA-256 is `b4d9103eee2e30edfc38d9cca41cfbe191a63b3051c3ee544699367cb550ee4d`. This report is a geometry comparison only, not a fabrication or engineering release.
