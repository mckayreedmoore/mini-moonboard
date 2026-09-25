# Second full-layout preflight failure

The parent run stopped after 1.261310 seconds before host machining or the
full-scene diagnostic. The compositor incorrectly removed newly replaced SDS
operations when comparing the complete source-cut maps to retained WJ18 maps.
Those maps retain all original source operations; a separate removed-cutter
set filters the final machining. WJ18's left-side map still contains the three
bottom-outer upright SDS operations. The correction must compare the complete
maps directly, preserving separate canonical-source, receiver-redirect and
removed-operation meanings. Exact failed source/test snapshots and unchanged
hashes are retained. No geometry pass or structural solve is established.
