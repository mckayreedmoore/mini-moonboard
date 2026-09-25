# Preserved bottom-center source ID guard failure

Retained-g18 attempt 02 stopped after 2.841 seconds in the candidate scene
guard. The guard expected `uncut_wood_parts()` to contain only the inventory's
20 timber members, but the source API returns all 26 wood items: 20 timber
members and six plywood panels. The source-bound filtered scene still needs to
retain exactly those inventory timber and panel IDs while excluding generated
clips and fasteners.

The [producer snapshot](producer.py.snapshot), [execution record](execution.json),
and [traceback](traceback.txt) preserve the failed attempt. No diagnostic
report or native solve was produced, and geometry was not changed.
