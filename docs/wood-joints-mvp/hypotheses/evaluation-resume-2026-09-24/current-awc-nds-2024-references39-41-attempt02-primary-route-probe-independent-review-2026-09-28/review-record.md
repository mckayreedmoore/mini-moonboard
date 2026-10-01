# Independent review record

**Review date:** 2026-09-28  
**Reviewed packet:** `current-awc-nds-2024-references39-41-attempt02-primary-route-probe-2026-09-28`  
**Scope:** local packet hashes and immutable source pins; distinctness of its five route probes from attempt01; disclosure/exclusion of the repeated landing-page request; and the limits of its access-failure conclusion.

## Verdict

**PASS — bounded route-probe and integrity review.** The packet verifier passes. Its four packet-file hashes and four immutable source pins match. Each of the five routes is a distinct AWC-hosted path or endpoint not recorded as a direct route in attempt01. My independent web-tool opens returned “not accessible via this tool” for all five, with no response bodies or HTTP statuses. The conclusion correctly remains about this tool's access failure and does not claim source absence.

The mutable queue digest is contextual and expressly excluded from verifier enforcement. Its recorded start-of-search digest differs from the live queue digest observed during this review; this does not invalidate the four immutable pins and cannot be used to retroactively validate the queue's state at the recorded start time.

## Route comparison

The five new probes are separate from attempt01's directly recorded resource page, viewer shortlink, LinkedIn announcement, press-release page, Chapter 11 PDF, and Accuris preview routes:

| Packet route | Route type | Independent web-tool result |
|---|---|---|
| `https://awc.org/wp-json/wp/v2/pages?slug=2024-nds` | WordPress REST pages resource, filtered by the NDS page slug | Not accessible via this tool |
| `https://awc.org/wp-json/wp/v2/media?search=NDS2024&per_page=100` | WordPress REST media resource, filtered by search and page-size parameters | Not accessible via this tool; the tool echoed the same query parameters in reversed order |
| `https://awc.org/wp-sitemap.xml` | Sitemap index path | Not accessible via this tool |
| `https://awc.org/wp-sitemap-posts-page-1.xml` | Page-post sitemap path | Not accessible via this tool |
| `https://awc.org/robots.txt` | Robots/crawl-policy path | Not accessible via this tool |

These are five distinct URLs. The two REST routes address different resources (`pages` and `media`); the sitemap index and page sitemap are separate paths; and `robots.txt` is a separate route. None appears among attempt01's recorded direct source URLs. A different route returning the same tool-level error is not content evidence about any endpoint.

## Repeated request audit

The attempt02 packet discloses that `https://awc.org/resources/2024-nds/` was accidentally included in the same browser batch and returned 403. It is placed in a separate `audit_note`, has `use_in_finding: false`, is absent from `new_official_routes_tested`, and the README explicitly excludes it from the result. I likewise excluded that repeated page from this review's new-route comparison and independent reprobes.

## Claim and source boundary

The packet records no response headers, HTTP status, redirect target, or body for any of the five route attempts, and it marks the References text as unobserved. Its conclusion says only that the routes did not return content through the available web tool and expressly says this does not establish absence. It neither authenticates References 39–41 nor promotes the attempt01 mirror transcription; it also does not establish a timber through-bolt `N+V+M` method.

This review received only tool error text for the five reprobes. No REST JSON, sitemap XML, robots text, AWC PDF or References-page bytes were retrieved or hashed. See [`integrity-checks.json`](integrity-checks.json) for local-file hashes and pin status.
