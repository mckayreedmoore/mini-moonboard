# T06 Goossens thesis source-route screen — attempt09

**Disposition:** The official KIT wood-structures thesis list confirms the
2017 title, author, and supervisor, but the bounded official KIT/KITopen,
library-catalog, and author/title searches in this attempt did not yield the
thesis PDF or a thesis-specific repository record with a download link.
This is a route-search result, **not evidence that the thesis is absent or
unavailable**. No content-level fact from the thesis is claimed. `steel_direct`
remains unresolved.

This append-only packet follows T06 attempt08. It changes no method, capacity,
criterion, hardware, candidate, geometry, solver state, or release status.
No external contact was made.

## Source observations

The official KIT completed-master-theses page lists *M-N-V Interaktion in
stiftförmigen Verbindungsmitteln für Stahlblech-Holzverbindungen* under 2017,
with Karena Goossens as author and Hans Joachim Blaß as supervisor. The row
does not expose a thesis-specific link, repository identifier, page count,
or download URL. The English-language version of the same official list
confirms the same metadata.

The official KITopen landing page for Blaß's 2018 chapter cites Goossens
(2017) as a KIT master thesis in its printed p. 25 bibliography. That is
publication-context metadata only; it does not expose the thesis or establish
any page-level thesis content. Searches restricted to KITopen and the KIT
library catalog did not surface a thesis record or bytes. Exact queries and
route outcomes are recorded in `source-observations.json`.

No target-thesis PDF, scan, repository object, or metadata export was obtained.
Accordingly, the following thesis-content questions remain **unobserved**:

| Required fact | Thesis observation in this attempt |
|---|---|
| Tension resistance and section/property basis | Not observed; thesis bytes unavailable through attempted routes. |
| Bending resistance and section basis | Not observed. |
| Shear resistance and section basis | Not observed. |
| Thread/root/stress-area basis or thread-to-shank transition | Not observed. |
| Fastener span, restraint, and local force distribution | Not observed. |
| Tests, benchmark, validation population, and limits | Not observed. |
| Design format, factors, and code/standard basis | Not observed. |

The thesis title scopes its subject to dowel-type fasteners in steel-sheet–wood
connections. Even if obtained, that subject alone would not establish transfer
to the reviewed timber-only through-bolt topology. The missing applicability
and section-level mechanics must be read from the thesis itself and assessed
against the current joint; no result can be inferred from the title or its
citation by Blaß.

## Exact route attempts

1. Opened the [official KIT completed-master-theses listing](https://holz.vaka.kit.edu/798.php)
   and its [English counterpart](https://holz.vaka.kit.edu/english/798.php).
   Both identify the thesis, author, supervisor, and 2017 listing. Neither
   provides a thesis-specific link in the row.
2. Searched KITopen with the exact title and author, including domain-limited
   queries for `publikationen.bibliothek.kit.edu`. Results returned the KIT
   completed-theses listing and related Blaß publications, but no thesis
   record or thesis bytes. Attempts to open
   `https://publikationen.bibliothek.kit.edu/?query=Goossens` and
   `https://publikationen.bibliothek.kit.edu/search?query=Goossens` were
   rejected as inaccessible by the web reader. The official 2017 archive URL
   `https://publikationen.bibliothek.kit.edu/index.php?hitsperpage=100&year=2017`
   produced a cache miss. These are reader/route outcomes, not repository
   availability findings.
3. Queried the KIT library catalog through exact-title/author searches scoped
   to `katalog.bibliothek.kit.edu` and `kvk.bibliothek.kit.edu`; no target
   record surfaced. Direct opens of the guessed Koha search URLs were rejected
   by the web reader. The catalog home page itself opened and showed a keyword
   search input, but this tool did not submit that form.
4. Searched the author and exact title for an author-facing repository route.
   No author-controlled repository record or thesis bytes surfaced. No
   author, supervisor, or library staff member was contacted.
5. Searched the German National Library domain for the exact title/author.
   The returned DNB result was the later Blaß 2018 chapter, not the Goossens
   thesis.

The query strings, URLs, host roles, and outcomes are machine-readable in
`source-observations.json`. Search results and browser extraction are recorded
as route evidence only; no external PDF byte hash is claimed.

## Next executable action

After parent validation of this packet, use the visible keyword-search form on
the official KIT library catalog home page with the exact thesis title and
`Karena Goossens`; if it returns a thesis record, follow its own full-text
link, preserve the landing-page metadata and downloaded PDF bytes, compute the
PDF SHA-256, and inspect page-located M/N/V, section, restraint, test, and design
format evidence. If it returns no record, report that exact result to the
parent and stop this source route without claiming the thesis is absent.

## Integrity and reproduction

Run from the repository root:

```sh
python3 docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-steel-direct-screen-attempt09-goossens-thesis-2026-09-28/verify_source_packet.py
cd docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-steel-direct-screen-attempt09-goossens-thesis-2026-09-28
sha256sum -c SHA256SUMS
```

The verifier checks local packet checksums and the immutable attempt08 pins. It
does not fetch web pages or claim to authenticate the external thesis PDF.
