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
  if (['eoere-selected-hardware-frame-development', 'eoere-selected-hardware-grid-development'].includes(model))
    return [
      {label: 'Current revision and evidence', path: current + 'README.md'},
      {label: 'Builder sequence and dimensions', path: current + 'builder-plan.md'},
      {label: 'Timber profiles and receiver datums', path: current + 'builder-layout.md'},
      {label: 'Selected 100 bolt stacks', path: evidence + 'shop-assembly-v1/extended-cleat-followup-v1/current-model-followup-v1/hardware-selection.csv'},
      {label: 'Selected hardware and nominal access', path: evidence + 'selected-hardware-v1/README.md'},
      {label: 'Six current cases · extra grid off', path: evidence + 'selected-hardware-v1/current-response-v1/result.json'},
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
