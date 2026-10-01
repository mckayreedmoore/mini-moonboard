# Independent follow-up — attempt05 AWC bibliography boundary

**Verdict: SUPPORTED.** Attempt05 addresses the attempt04 wording note: it now
states that the 2021 FAQ does not identify the NDS edition its entries describe,
contrasts the FAQ only with the official 2018 list, and leaves the 2024 mapping
provisional.

## Findings

- The [AWC 2018 NDS References PDF](https://awc.org/wp-content/uploads/2021/10/AWC_NDS2018-withCommentary_20200827_AWCWebsite_References.pdf),
  printed page 191, confirms ref. 39 = RCSC 2009, ref. 40 = ANSI/AISC 360-10
  (2010), and ref. 41 = AISI 2007. Attempt05 transcribes these accurately.
- The [AWC FAQ](https://awc.org/faq/where-can-i-find-more-information-on-all-of-the-nds-references/)
  is dated September 27, 2021 and displays different, older publications for
  entries 39–41. It does not identify the NDS edition for that list. The direct
  page request returned 403; the official indexed result supplied the entries.
- The [AWC 2024 NDS page](https://awc.org/resources/2024-nds/) confirms the
  2024 edition and offers a free view-only option, but the page content does not
  provide References 39–41. It does not authenticate the mirror-derived map.
- No design method, capacity, criterion disposition, or release state is
  asserted or changed by attempt05. Keeping `steel_direct` at `SOURCE_GAP` is a
  preserved disposition, not a new mechanics conclusion.

The opening phrase “official AWC materials for older NDS editions” could be
read as assigning the 2021 FAQ to an older edition. The body and source record
explicitly say that edition is unknown, and the stated decision does not depend
on assigning one. For maximum precision, the opening could say “an official
2018 NDS list and a separate AWC FAQ with an unidentified list edition.” This
is a non-blocking style note; the attempt04 finding is substantively resolved.

## Integrity

All three attempt05 files are bound by SHA-256 in
[`review-record.json`](review-record.json). The files in this review packet are
bound by [`SHA256SUMS`](SHA256SUMS). The source-edition check used official AWC
links above; no native or solver work was performed, and no candidate or
release state was changed.
