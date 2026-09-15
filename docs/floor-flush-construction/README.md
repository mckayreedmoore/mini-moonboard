# Flush floor-beam construction coordinates — draft

**Geometry reference only. Current resistance and fabrication gates remain open;
these are not released cut or drilling instructions.**

Candidate: `compact-floor-flush-development`. See
[the current package](../floor-flush-build-package.md) for completion status.

- `stock.csv` gives stock allowances, not finished lengths.
- `stock-profiles.json` records actual trimmed raw timber vertices in world millimetres.
- Eight `*-bolt-sheet.svg` sheets show those actual profiles and relocated bolt axes.
- `bolt-member-datums.csv` and `profile-corner-datums.csv` share a physical corner datum,
  along-grain A and signed cross-grain C. Identify the corner on the sheet before layout.
- Leg taper sheets and `leg-taper-cuts.csv` specify separate inner-face removal.
- `runner-end-geometry.json` records the square front and inclined rear cut endpoints.
- `connection-axes.csv`, `panel-attachment-axes.csv`, `panel-hole-axes.csv` and
  `timber-passages.json` retain the current screw, panel and passage coordinates.
- `bolt-hardware.csv` describes current catalog bolt stacks; drawing precision does
  not establish fabrication tolerance, pilot bits, acceptable substitutions or capacity.

Use numerical coordinates, not image scale. Left and right use their own physical
minimum-X datum: do not mirror a datum convention blindly. Kickers remain whole.
All timber profiles assume fresh stock; previous holes are not repair instructions.
