# Viewer control-panel evaluation

Evaluated September 11, 2026 against the [published Mini 2020 viewer](https://mckayreedmoore.github.io/mini-moonboard/?setup=2020), with the round-bore frame selected. This evaluates the existing control panel, before the new problem-highlighting controls. Findings combine source inspection of `site/index.html` with Chromium screenshots and DOM measurements at 1600 × 1100, 768 × 1024, and 390 × 844.

The panel works as an engineering inspection toolbox, but its growing document and frame information obscures the newer hold-viewing tasks. The best next change is a smaller, collapsible panel with visible selection feedback and separate disclosures for holds, frame inspection, and documents. A new framework or a full navigation system is unnecessary.

## Findings, in priority order

1. **Selection feedback is hidden during normal use.** At desktop size the panel is 495 px tall, while the selected-item card starts 641 px below its top. On the phone the panel is 380 px tall and that card starts at 765 px. Clicking a hold updates text below the visible region without revealing or announcing it. Keep a short selection summary beside the active controls, expose longer details on demand, and announce selection changes through a polite status region. Preserve panel scroll position rather than forcing a scroll after every click.

2. **The panel consumes too much space on phones.** The full-width overlay occupies 45% of the phone viewport; its content requires 1,088 px of vertical space. In the initial view it covers the board's top and leaves the board small. The existing front-view button improves camera framing, but users must discover it first. Add a clearly labeled collapse/expand control, retain a small setup and view toolbar when collapsed, and fit the initial board to the usable viewport. Recompute framing when the panel changes size. Do not reduce type size to fit more controls.

3. **Different tasks share one long scroll region.** Draft documents precede hold controls; detailed weight assumptions precede connection inspection; the design picker sits below the selected-item card and donation link. Put the active setup, view action, and selection first. Group existing controls under native disclosures named Holds, Frame inspection, and Documents. Keep the current frame's unqualified status visible; move extended weight assumptions and historical design explanations into details. Keep all current documents accessible.

4. **The desktop design selector overflows horizontally.** Measured panel `scrollWidth` is 535 px against a 512 px `clientWidth`; the selector itself is 509 px wide before its label and panel padding. The mobile-only width rule prevents this at 390 px, but desktop still gains sideways overflow. Constrain selects to the available width at every breakpoint. Use short option labels and show the full chosen design description below the picker.

5. **Touch and keyboard interaction need deliberate support.** The front button is about 27 px tall; checkbox rows are about 18 px apart. The labels enlarge checkbox hit areas, but these tightly packed rows remain easy to mistap. Increase row spacing and primary controls toward 44 px touch targets. Native labeled inputs, the visibility fieldset, and hold-loading status are good foundations. However, individual holds currently require canvas pointer picking: provide a labeled grid-position input or list for keyboard selection and problem editing. This is a targeted usability review, not a complete accessibility conformance audit.

## New problem controls

The parallel implementation proposes a collapsed “Problem” disclosure inside the hold controls, with an explicit editing toggle, a role selector, a text-and-color legend, marked positions, Clear, and Copy link. Collapsing it by default is appropriate and avoids adding the whole editor to the initial panel. It does not resolve the existing hidden selection feedback, mobile coverage, or keyboard hold selection. Review the expanded state at phone width and ensure edit mode is unmistakable before relying on it for route entry. Pending controls were not present in the published screenshots and are not treated as verified here.

## Verification for a panel revision

Check desktop, tablet, and 390 px phone widths with the panel expanded and collapsed; require no horizontal overflow. A selected hold's name must remain visible without manually scrolling the panel. Verify keyboard setup changes, selection, and problem editing, along with touch-sized controls and front framing after disclosure changes. Preserve setup/model URL state, part visibility, and restoration from connection inspection.

Local screenshots: `fea/generated/viewer-ui-evaluation/sidebar-desktop.png` `sidebar-tablet.png`, and `sidebar-phone.png`. These generated review artifacts are not publication assets.
