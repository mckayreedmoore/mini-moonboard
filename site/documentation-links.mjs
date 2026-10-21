// Presentation routing only. Frozen scene metadata keeps its original paths.
const movedDocuments = new Set([
  'compact-construction-package.md', 'compact-splice-study.md',
  'compact-spliced-build-package.md', 'compact-thick-study.md',
  'disassembly-guide.md', 'floor-runner-recess-study.md',
  'floor-runner-taper-study.md', 'horizontal-service-build-plan.md',
  'horizontal-service-drilling.md', 'leg-150-comparison.md',
  'leg-completion-decision.md', 'leg-material-basis.md',
  'no-shoes-candidate.md', 'round-insert-build-plan.md',
  'round-reinforcement-development.md', 'round-service-build-plan.md',
  'round-structural-build-plan.md', 'thick-leg-pivot-study.md',
  'threaded-insert-repair-guide.md', 'wider-leg-decision.md',
  'wider-leg-hardware.md',
]);

export function resolveDocumentPath(path) {
  const match = /^docs\/([^/?#]+)(.*)$/.exec(path);
  return match && movedDocuments.has(match[1]) ? `docs/history/${match[1]}${match[2]}` : path;
}

const evidence = 'docs/wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/';
const current = 'docs/bolted-frame-development/';
const ledger = 'docs/wood-joints-mvp/completion-ledger.md';
const preservedEoere = {
  'eoere-bolted-development': 'occupied-geometry-v2.json',
  'eoere-bolted-bottom-rail-development': 'occupied-bottom-rail-v1.json',
  'eoere-bolted-trimmed-cleats-development': 'occupied-cleat-trim-v1.json',
  'eoere-bolted-aligned-wire-development': 'occupied-aligned-wire-v1.json',
  'eoere-adjusted-frame-development': 'occupied-adjusted-base-v3.json',
  'eoere-new-2026-adjustments': 'occupied-2026-adjustments-v3.json',
  'eoere-extended-cleat-frame-development': 'occupied-extended-cleats-v1.json',
  'eoere-extended-cleat-2026-development': 'occupied-extended-cleats-v1.json',
  'eoere-uniform-channels-frame-development': 'occupied-uniform-channels-v1.json',
  'eoere-uniform-channels-2026-development': 'occupied-uniform-channels-v1.json',
  'eoere-kicker-clearance-frame-development': 'occupied-kicker-clearance-v1.json',
  'eoere-kicker-clearance-2026-development': 'occupied-kicker-clearance-v1.json',
  'eoere-expanded-right-column-development': 'occupied-right-column-v1.json',
};

export function documentsForModel(model, recordedDocuments = []) {
  if (model === 'eoere-leg-header-frame-development')
    return [
      {label: 'Current builder plan · single leg bolts and plywood cleats', path: current + 'builder-plan.md'},
      {label: '96-axis member and receiver layout', path: current + 'builder-layout.md'},
      {label: 'Combined geometry and hardware receipt', path: evidence + 'leg-header-v3/geometry.json'},
      {label: '96 selected bolt stacks and spacers', path: evidence + 'leg-header-v3/hardware-selection.csv'},
      {label: '32 retained enclosed-passage datums', path: evidence + 'enclosed-passages-v1/passage-datums.csv'},
      {label: 'Current calculations and remaining holds', path: ledger + '#single-bolt-leg-joint-review'},
    ];
  if (model === 'eoere-enclosed-passages-frame-development')
    return [
      {label: 'Current builder plan · 96-bolt successor', path: current + 'builder-plan.md'},
      {label: 'Current member and receiver layout', path: current + 'builder-layout.md'},
      {label: '32 enclosed-passage datums', path: evidence + 'enclosed-passages-v1/passage-datums.csv'},
      {label: 'Enclosed-passage geometry receipt', path: evidence + 'enclosed-passages-v1/geometry.json'},
      {label: 'Passage section diagram', path: current + 'enclosed-passage-study.svg'},
      {label: 'Six preceding cases · extra grid off · earlier geometry', path: evidence + 'selected-hardware-v1/current-response-v1/result.json'},
    ];
  if (['eoere-narrow-channels-frame-development', 'eoere-narrow-channels-grid-development'].includes(model))
    return [
      {label: 'Current builder plan · 96-bolt successor', path: current + 'builder-plan.md'},
      {label: 'Current member and receiver layout', path: current + 'builder-layout.md'},
      {label: '32 narrowed channel datums', path: evidence + 'narrow-channels-v1/service-channel-datums.csv'},
      {label: 'Preserved narrower-channel geometry receipt', path: evidence + 'occupied-narrow-channels-v1.json'},
      {label: 'Six preceding cases · extra grid off', path: evidence + 'selected-hardware-v1/current-response-v1/result.json'},
      {label: 'Notch-size revision and retained holds', path: ledger + '#current-narrow-channel-revision'},
    ];
  if (['eoere-4x6-front-posts-frame-development', 'eoere-4x6-front-posts-grid-development'].includes(model))
    return [
      {label: 'Current revision and evidence', path: current + 'README.md'},
      {label: 'Builder sequence and dimensions', path: current + 'builder-plan.md'},
      {label: 'Timber profiles and receiver datums', path: current + 'builder-layout.md'},
      {label: '4×6 post geometry and bounded checks', path: evidence + 'occupied-front-posts-4x6-v1.json'},
      {label: 'Eight revised bolt stacks', path: evidence + 'front-posts-4x6-v1/hardware-selection.csv'},
      {label: 'Six preceding cases · 2×6 posts, extra grid off', path: evidence + 'selected-hardware-v1/current-response-v1/result.json'},
      {label: 'Current post revision and remaining checks', path: ledger + '#current-4x6-front-post-revision'},
    ];
  if (['eoere-selected-hardware-frame-development', 'eoere-selected-hardware-grid-development'].includes(model))
    return [
      {label: 'Preserved 2×6-post shop packet', path: evidence + 'shop-assembly-v1/extended-cleat-followup-v1/current-model-followup-v1/README.md'},
      {label: 'Active development · separate revision', path: current + 'README.md'},
      {label: 'Selected 100 bolt stacks', path: evidence + 'shop-assembly-v1/extended-cleat-followup-v1/current-model-followup-v1/hardware-selection.csv'},
      {label: 'Selected hardware and nominal access', path: evidence + 'selected-hardware-v1/README.md'},
      {label: 'Six matching 2×6-post cases · extra grid off', path: evidence + 'selected-hardware-v1/current-response-v1/result.json'},
      {label: 'Qualification limits and owner deferrals', path: ledger + '#engineering-closure-beyond-the-assessment'},
    ];
  if (model === 'eoere-lower-cleat-z180-development')
    return [
      {label: 'Unadopted Z180 nominal shop records', path: evidence + 'shop-assembly-v1/extended-cleat-followup-v1/z180-proposal-v1/README.md'},
      {label: 'Z180 own-case numerical results and limits', path: ledger + '#lowered-cleat-bolt-proposal-conditional-numerical-completion'},
      {label: 'Current Z200 revision and evidence', path: current + 'README.md'},
    ];
  if (['wood-joints-reviewed', 'wood-joints-working-proposal'].includes(model))
    return [
      {label: 'Preserved reviewed 104-bolt authority', path: 'wood-joints-candidate.json'},
      {label: 'Preserved wood-joint packet and limits', path: 'docs/history/design-history.md#milestones-and-what-they-taught-us'},
      {label: 'Unadopted 108-bolt knee bridge package', path: 'docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/knee-bridge-working-package.md'},
    ];
  if (Object.hasOwn(preservedEoere, model))
    return [
      {label: 'Preserved frame geometry receipt', path: evidence + preservedEoere[model]},
      {label: 'Historical revisions, optional layers and numerical scope', path: 'docs/history/design-history.md#eoere-development-sequence'},
      {label: 'Active development summary · separate revision', path: current + 'README.md'},
    ];
  if (model === 'thin-bolted-development')
    return [
      {label: 'Preserved thin-frame authority', path: 'thin-bolted-candidate.json'},
      {label: 'Preserved thin-frame evidence and limits', path: ledger + '#hl35-replacement-candidate'},
      {label: 'Active development summary · separate revision', path: current + 'README.md'},
    ];
  if (['hl35-development', 'hl35-fit-development', 'hl35-counterbore-development'].includes(model))
    return recordedDocuments.map(row => row.path === ledger
      ? {...row, label: 'Preserved HL35 development and limits', path: ledger + '#hl35-replacement-candidate'}
      : row);
  return recordedDocuments;
}
