# WJ24 viewer review

## Earlier owner-directed design review, superseded

This review describes the predecessor model. The current WJ24 viewer uses
`outer-rear-bridges-under-header-links-removed-v1`; see the [current outer-support
removal checkpoint](hypotheses/outer-links-removed-2026-09-24/README.md). The
snapshots and hashes below are preserved evidence for this earlier revision.

At the time of this review, the local [WJ24 viewer](../../site/wood-joints-wj24-viewer.html) read the isolated `owner_wood_joints_design_review_scene/v1` branch at the same URL. The reviewed revision was `lower-rear-blocks-below-plus-bottom-support-up-one-row-v1`: the middle rear blocks were below their rails and the bottom support was raised one hold row. The page reported design-review status, showed only that revision's findings, and stated that earlier static or diagnostic passes did not carry forward. Its link to the [frame-to-kicker options](../../site/wood-joints-kicker-options.html) sat below that revision summary; no option was selected.

The final viewer source SHA-256 is `3afb271aa1403e839f6382f78d6a120e1f00429c2bd3ec870fa7c923ec138669`. The current scene payload is 9,335,595 bytes with SHA-256 `bf68c4247e1a99b1c7d5bad02b0fe5f6b9ddec34a47e1dca6d41edd2ad731389`; its revision report SHA-256 is `bf8392ff07d213525e7032802979c887c9de53540361844aa84cc9e740ce1c33`. The scene binds source inventory SHA-256 `07af4c3eb642cf3887595fe4415eb65404cdcf74d66c5c7bb182847ef21c2d78` and the preserved parent scene SHA-256 `b80baec6b4435f4cfad724efdc25df787d04251f1a1b7203ba63782fb4b485f0`.

The current overlay has 568 solids: 16 shared hosts, 28 candidate parts, 520 hardware occupancy envelopes, and four panel replacements. Of the 725 hashed baseline assets, 537 are rendered once and 188 replaced visuals are suppressed. The panel-screw identities comprise 62 unchanged axes and four moved axes whose baseline STL instances use explicit display translations; the twelve starting frame-bolt arrangements remain in the baseline. Every acceptance and release flag remains false.

The parent-run Chromium review passed all three camera buttons and all five layer controls at the cumulative 568-solid geometry. It recorded 537 visible / 188 suppressed baseline visuals, a successful 390×844 mobile layout, and no page errors or failed requests. The parent visually reviewed the full-frame view and confirmed the blocks below the middle rails and the raised bottom support are visible. Browser screenshots, result JSON, current scene/report/source snapshots, and their manifest are in the [owner-directed design-review archive](hypotheses/wj24-owner-design-review-2026-09-24/README.md). The screenshots predate a later caption-only report refresh and the final placement of the options link; the archive records that provenance and provides the separately captured browser-session HTML snapshot. Screen-reader verification remains pending.

## Earlier integrated-static viewer review

The earlier scene used the `REVISE` diagnostic schema and was reviewed against the [integrated-static source record](hypotheses/wj24-integrated-static/README.md). Its pinned payload had SHA-256 `b80baec6b4435f4cfad724efdc25df787d04251f1a1b7203ba63782fb4b485f0` and its reviewed HTML had SHA-256 `4e505823957e5271963bac629fa87e282e6e368d3a58e8fd5a577b9148ccd16d`. The archived browser review covered keyboard rotation/zoom, 44-pixel controls, 390×844 and 320×568 mobile layouts, six finding cards, and the earlier false-release status. Those results describe the older scene only; the preserved [original viewer archive](hypotheses/wj24-viewer-review/README.md) is unchanged and its static passes are not inherited by the current owner-directed design review.
