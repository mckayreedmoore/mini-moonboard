# Half-timestep early output prefix

This immutable snapshot preserves four accepted increments of the live
half-timestep diagnostic through 0.002 s. Their iteration counts are 23, 5,
7 and 8; the captured status file has no rejected attempts. The source case
continues independently of this snapshot.

The parent verified all 34 input artifact hashes before capture. Each output
was copied through its size when opened, with the status file first; files
are not atomic with one another. Only complete output blocks at accepted
status times may be compared. Missing or partial records are unavailable,
not zero. The preserved execution record is a nonterminal observation, not
the final outcome. Its inherited input-only scope text describes preparation;
the status and native output establish that execution has begun.

The [snapshot manifest](snapshot.json), SHA-256
`07566ead8aa5e7c9b48d0bbd1a026240c507cd2da805d5dc9a256eccb21c1483`,
pins the captured bytes and their source. The input-freeze SHA-256 is
`ea24423f587795743d0c1189c798f77d83159208c76d5d1d3a9fa5554eda4f56`.
The exact early common times with the coarse run are 0.001 and 0.002 s.
This capture alone establishes no timestep accuracy or mechanical acceptance.
