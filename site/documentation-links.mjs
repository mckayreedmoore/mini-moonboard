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
  if (model === 'eoere-v11-matching-rear-bolts-preview')
    return [
      {label: 'Unselected matching rear-bolt trial and remaining checks', path: current + 'owner-frame-v11/matching-rear-bolts/README.md'},
      {label: 'Own matching rear-bolt geometry receipt', path: current + 'owner-frame-v11/matching-rear-bolts/geometry-receipt.json'},
      {label: 'Own six-case bank and twelve replays', path: current + 'owner-frame-v11/matching-rear-bolts/response-bank.json'},
      {label: 'Own conditional references and unresolved connections', path: current + 'owner-frame-v11/matching-rear-bolts/reference-completion.json'},
      {label: 'Development status and remaining work', path: current + 'README.md'},
      {label: 'Builder scope and holds', path: current + 'builder-plan.md'},
    ];
  if (model === 'eoere-v11-shorter-bolts-preview')
    return [
      {label: 'Own shorter-bolt geometry receipt', path: current + 'owner-frame-v11/shorter-bolts/geometry-receipt.json'},
      {label: 'Own six-case bank and twelve replays', path: current + 'owner-frame-v11/shorter-bolts/response-bank.json'},
      {label: 'Current conditional references and unresolved connections', path: current + 'owner-frame-v11/shorter-bolts/reference-review.json'},
      {label: 'Current-pattern connection checks and remaining duties', path: current + 'owner-frame-v11/shorter-bolts/joint-disposition.json'},
      {label: 'Additional joint criteria and exact bearing bounds (compressed JSON)', path: current + 'owner-frame-v11/shorter-bolts/joint-criterion-followthrough.json.gz'},
      {label: 'Provisional bolt list, member plan and printable marking tools', path: current + 'owner-frame-v11/shorter-bolts/build-package/README.md'},
      {label: 'Separate diagnostic and scenario flag rows', path: current + 'owner-frame-v11/shorter-bolts/numerical-flag-inventory.csv'},
      {label: 'Owner shorter-bolt freeze exception', path: current + 'owner-frame-v11/owner-shorter-bolt-exemption.json'},
      {label: 'Development status and remaining work', path: current + 'README.md'},
      {label: 'Builder scope and holds', path: current + 'builder-plan.md'},
    ];
  if (model === 'eoere-v11-v9-eight-bolt-preview')
    return [
      {label: 'Owner V9-based eight-bolt request', path: current + 'owner-frame-v11/owner-v9-eight-bolt-request.json'},
      {label: 'Frozen geometry-only receipt', path: current + 'owner-frame-v11/geometry-receipt.json'},
      {label: 'Own six-case bank and twelve replays', path: current + 'owner-frame-v11/response-bank.json'},
      {label: 'Current conditional member and cleat review', path: current + 'owner-frame-v11/reference-review.json'},
      {label: 'Physical-row connection references and unresolved criteria', path: current + 'owner-frame-v11/connection-capacity-followthrough.json'},
      {label: 'Conditional Grade 5 property comparison; same force bank', path: current + 'owner-frame-v11/grade5-property-comparison.json'},
      {label: 'Current Grade 5 row bounds; inconclusive flags retained', path: current + 'owner-frame-v11/grade5-row-comparison.json'},
      {label: 'Standard NDS group equations and fixed row hypotheses', path: current + 'owner-frame-v11/standard-cg-comparison.json'},
      {label: 'Mixed planes, fitting, geometry and nominal hardware follow-through', path: current + 'owner-frame-v11/criterion-followthrough.json'},
      {label: 'Nominal hardware body/root diameter clarification', path: current + 'owner-frame-v11/hardware-thread-diameter-addendum.json'},
      {label: 'Owner material assumptions and hardware purchase status', path: current + 'owner-frame-v11/owner-material-purchase-decisions.json'},
      {label: 'Current signed end, edge and row geometry checks', path: current + 'owner-frame-v11/geometry-applicability.json'},
      {label: 'Current washer and fitting references', path: current + 'owner-frame-v11/component-reference-summary.json'},
      {label: 'Development status and remaining work', path: current + 'README.md'},
      {label: 'Builder scope and holds', path: current + 'builder-plan.md'},
    ];
  if (model === 'eoere-packer-free-center-far-row-preview')
    return [
      {label: 'Current development and trial status', path: current + 'README.md'},
      {label: 'Builder scope and holds', path: current + 'builder-plan.md'},
      {label: 'Owner direction: no wood packers', path: current + 'owner-frame-v10/owner-no-wood-packers-v1.json'},
    ];
  if (model === 'eoere-packer-free-standard-stock-preview')
    return [
      {label: 'Own six-case response bank', path: 'docs/bolted-frame-development/owner-frame-v10/packer-free/response-bank.json'},
      {label: 'Current connection methods and remaining inputs', path: 'docs/bolted-frame-development/owner-frame-v10/packer-free/connection-method-evaluation.json'},
      {label: 'Packer-free geometry receipt', path: current + 'owner-frame-v10/packer-free/geometry-receipt.json'},
      {label: 'Own six-case conditional assessment', path: current + 'owner-frame-v10/packer-free/evaluation.json'},
      {label: 'Development status and remaining work', path: current + 'README.md'},
      {label: 'Owner direction: no wood packers', path: current + 'owner-frame-v10/owner-no-wood-packers-v1.json'},
      {label: 'Builder scope and holds', path: current + 'builder-plan.md'},
    ];
  if (model === 'eoere-standard-4x6-top-and-sides-preview')
    return [
      {label: 'Current standard-stock development', path: 'docs/bolted-frame-development/README.md'},
      {label: 'Current completion and remaining work', path: 'docs/wood-joints-mvp/completion-ledger.md#current-v10-standard-top-and-sides'},
      {label: 'Current geometry receipt', path: 'docs/bolted-frame-development/owner-frame-v10/standard-side-stock/geometry-receipt.json'},
      {label: 'Current connection methods', path: 'docs/bolted-frame-development/owner-frame-v10/standard-side-stock/connection-method-evaluation.json'},
      {label: 'Provisional wood procurement', path: 'docs/bolted-frame-development/owner-frame-v10/standard-stock-planning.md'},
      {label: 'Builder scope and holds', path: 'docs/bolted-frame-development/builder-plan.md'},
    ];
  if (['eoere-current-frame-development', 'eoere-owner-frame-v10-development'].includes(model))
    return [
      {"label": "Read first: corrected center-principal edge classification", "path": "docs/bolted-frame-development/owner-frame-v10/candidate13/paper-audit/center-principal-correction-13-v1.txt"},
      {"label": "Corrected package completion index", "path": "docs/bolted-frame-development/owner-frame-v10/candidate13/paper-audit/completion-index-v3.json"},
      {"label": "Group assessment and relocation limits", "path": "docs/bolted-frame-development/owner-frame-v10/candidate13/paper-audit/wsl-group-and-relocation-handoff-v1.txt"},

      {
        "label": "V10 development status and remaining checks",
        "path": "docs/bolted-frame-development/README.md"
      },
      {
        "label": "Candidate 13 layout and source boundaries",
        "path": "docs/bolted-frame-development/owner-frame-v10/layout.md"
      },
      {
        "label": "Frozen geometry receipt",
        "path": "docs/bolted-frame-development/owner-frame-v10/candidate13/geometry-receipt-13.json"
      },
      {
        "label": "Own six-case response bank",
        "path": "docs/bolted-frame-development/owner-frame-v10/candidate13/response-bank-13.json"
      },
      {
        "label": "Component references and remaining flags",
        "path": "docs/bolted-frame-development/owner-frame-v10/candidate13/reference-review-13.json"
      },
      {
        "label": "Canonical joint applicability and open qualifications",
        "path": "docs/bolted-frame-development/owner-frame-v10/candidate13/joint-applicability-13-canonical-wsl.json"
      },
      {
        "label": "Hardware and material planning holds",
        "path": "docs/bolted-frame-development/owner-frame-v10/candidate13/packet-13-complete/readiness.json"
      },
      {
        "label": "Hardware planning quantities",
        "path": "docs/bolted-frame-development/owner-frame-v10/candidate13/packet-13-complete/hardware-bom.csv"
      },
      {
        "label": "Candidate cut planning data",
        "path": "docs/bolted-frame-development/owner-frame-v10/candidate13/packet-13-complete/cut-plan.csv"
      },
      {
        "label": "Candidate bore planning data",
        "path": "docs/bolted-frame-development/owner-frame-v10/candidate13/packet-13-complete/drill-plan.csv"
      },
      {
        "label": "Frozen 29-artifact delivery manifest",
        "path": "docs/bolted-frame-development/owner-frame-v10/candidate13/delivery-bundle-13.json"
      },
      {
        "label": "Additive paper audit and method limits",
        "path": "docs/bolted-frame-development/owner-frame-v10/candidate13/paper-audit/candidate13-paper-audit-summary-v1.txt"
      },
      {
        "label": "Paper audit source bindings",
        "path": "docs/bolted-frame-development/owner-frame-v10/candidate13/paper-audit/paper-audit-bundle-v1.json"
      }
    ,
      {label: 'Conditional Candidate 13 builder sequence', path: current + 'owner-frame-v10/candidate13/packet-13-complete/builder-plan.md'},
      {label: 'Current scope and preserved instructions', path: current + 'builder-plan.md'},
      {label: 'Current integration and engineering ledger', path: ledger + '#current-v10-candidate13'}
    ];
  if (model === 'eoere-owner-frame-v9-development')
    return [
      {label: 'Current design and outstanding checks', path: current + 'README.md'},
      {label: 'Current shorter cleat bolts and single spacers · geometry receipt', path: current + 'owner-frame-v9/geometry.json'},
      {label: 'Eight changed hardware selections and catalog checks', path: current + 'owner-frame-v9/layout.md'},
      {label: 'Current mechanics input delta · no old force transfer', path: current + 'owner-frame-v9/mechanics-input-delta.json'},
      {label: 'Own six-case 250 lb response and independent replays', path: current + 'owner-frame-v9/response-bank.json'},
      {label: 'Current bolt geometry and unresolved complete joints', path: current + 'owner-frame-v9/bolt-geometry-review.json'},
      {label: 'Current bolt, timber and cleat reference comparisons', path: current + 'owner-frame-v9/reference-review.json'},
      {label: 'Current modeled panel and screw bracing contribution', path: current + 'owner-frame-v9/panel-bracing-review.json'},
      {label: 'Current changed axes, receivers and 78 bore rows', path: current + 'owner-frame-v8/layout.md'},
      {label: 'All 40 inward-facing exterior stacks and retained spacer lengths', path: current + 'owner-frame-v7/orientation.json'},
      {label: 'Preceding six-case 250 lb review · exterior-nut orientation', path: current + 'owner-frame-v6/engineering-review.json'},
      {label: 'Preceding testing correction and method limits', path: current + 'owner-frame-v6/testing-review.json'},
      {label: 'Preceding bolt geometry rules and unresolved oblique joints', path: current + 'owner-frame-v6/bolt-geometry-review-v2.json'},
      {label: 'Two restored center principal axes', path: current + 'owner-frame-v6/axes-additions.json'},
      {label: 'Updated principal member and receiver review', path: current + 'owner-frame-v6/layout.md'},
      {label: 'Straight-sided four-hole cleat drawings', path: current + 'owner-frame-v5/layout.md'},
      {label: 'Two added nominal center bolt stacks', path: current + 'owner-frame-v6/hardware-additions.csv'},
      {label: 'Current scope and preserved assembly instructions', path: current + 'builder-plan.md'},
      {label: 'Paired-bolt update and conditional bolt-039 remedy', path: ledger + '#current-principal-pair-revision'},
      {label: 'Inward-nut change and spacer explanation', path: ledger + '#current-inward-bolts'},
      {label: 'Cumulative angle revision and next checks', path: ledger + '#current-inward-angles'},
      {label: 'Single-spacer selection, checks and next actions', path: ledger + '#current-single-spacer-stacks'},
      {label: 'Preceding v6 panel/screw bracing study · no current force transfer', path: current + 'owner-frame-v6/panel-bracing-review.json'},
    ];
  if (model === 'eoere-owner-frame-v8-development')
    return [
      {label: 'Preserved inward bolts and inset angles before shorter hardware', path: current + 'owner-frame-v8/geometry.json'},
      {label: 'Own six-case response bank · before hardware change', path: current + 'owner-frame-v8/response-bank.json'},
      {label: 'Own unresolved bolt geometry review', path: current + 'owner-frame-v8/bolt-geometry-review.json'},
      {label: 'Current shorter hardware', path: current + 'owner-frame-v9/layout.md'},
    ];
  if (model === 'eoere-owner-frame-v7-development')
    return [
      {label: 'Preserved inward nuts before angle move', path: current + 'owner-frame-v7/geometry.json'},
      {label: 'Forty stack reversals and unchanged hardware lengths', path: current + 'owner-frame-v7/orientation.json'},
      {label: 'Current cumulative angle revision', path: current + 'owner-frame-v8/layout.md'},
    ];
  if (model === 'eoere-owner-frame-v6-development')
    return [
      {label: 'Preserved exterior-nut geometry', path: current + 'owner-frame-v6/geometry.json'},
      {label: 'Own six-case 250 lb review', path: current + 'owner-frame-v6/engineering-review.json'},
      {label: 'Own testing correction and method limits', path: current + 'owner-frame-v6/testing-review.json'},
      {label: 'Current orientation change', path: ledger + '#current-inward-bolts'},
    ];
  if (model === 'eoere-owner-frame-v5-development')
    return [
      {label: 'Current design and outstanding checks', path: current + 'README.md'},
      {label: 'Reference cleat revision and two restored upper bolts', path: current + 'owner-frame-v5/geometry.json'},
      {label: '94 axes and retained 66 screw locations', path: current + 'owner-frame-v5/axes.json'},
      {label: 'Current cleat review drawings and receiver coordinates', path: current + 'owner-frame-v5/layout.md'},
      {label: 'Two added nominal upper bolt stacks', path: current + 'owner-frame-v5/hardware-additions.csv'},
      {label: 'Preceding 92-bolt strength results · different geometry', path: current + 'owner-frame-v4/engineering-review.json'},
      {label: 'Current scope and preserved assembly instructions', path: current + 'builder-plan.md'},
      {label: 'Reference cleat changes and open upper-pair checks', path: ledger + '#current-reference-cleat-revision'},
    ];
  if (model === 'eoere-owner-frame-v4-development')
    return [
      {label: 'Current design and outstanding checks', path: current + 'README.md'},
      {label: 'Current front-bolt revision and retained geometry', path: current + 'owner-frame-v4/geometry.json'},
      {label: '92 axes and retained 66 screw locations', path: current + 'owner-frame-v4/axes.json'},
      {label: 'Current nominal hardware review · no build selection', path: current + 'owner-frame-v3/hardware-review.csv'},
      {label: 'Own revised bolt, cleat and timber results', path: current + 'owner-frame-v4/engineering-review.json'},
      {label: 'Revised front-post and runner drawings', path: current + 'owner-frame-v4/layout.md'},
      {label: 'Current scope and preserved assembly instructions', path: current + 'builder-plan.md'},
      {label: 'Current local changes and rejected geometry trials', path: ledger + '#current-front-bolt-moves'},
    ];
  if (model === 'eoere-owner-frame-v3-development')
    return [
      {label: 'Preserved geometry before the front-bolt move', path: current + 'owner-frame-v3/geometry.json'},
      {label: 'Preserved 50/100 mm front layout', path: current + 'owner-frame-v3/layout.md'},
      {label: 'Preserved bonded-frame engineering review', path: current + 'owner-frame-v3/engineering-review.json'},
    ];
  if (model === 'eoere-retained-2x6-frame-development')
    return [
      {label: 'Current scope and preserved 102-bolt instructions', path: current + 'builder-plan.md'},
      {label: 'Preserved 102-axis member and receiver layout', path: current + 'builder-layout.md'},
      {label: 'Preserved extended-top geometry receipt', path: current + 'paired-frame-v2/geometry.json'},
      {label: 'Preserved 102 selected bolt stacks', path: current + 'paired-frame-v2/hardware-selection.csv'},
      {label: 'Preserved stock allocation and hardware totals', path: current + 'paired-frame-v2/stock-nesting.csv'},
      {label: 'Current scope and preceding frame evaluation', path: ledger + '#paired-frame-completion-goal'},
    ];
  if (model === 'eoere-paired-cleats-frame-development')
    return [
      {label: 'Preserved paired-frame member stock', path: current + 'paired-frame-v1/members.csv'},
      {label: 'Preserved 134 receiver occurrences', path: current + 'paired-frame-v1/receiver-holes.csv'},
      {label: 'Preserved 106-bolt geometry receipt', path: current + 'paired-frame-v1/geometry.json'},
      {label: '106 selected bolt stacks and spacers', path: current + 'paired-frame-v1/hardware-selection.csv'},
      {label: '32 retained enclosed-passage datums', path: evidence + 'enclosed-passages-v1/passage-datums.csv'},
      {label: 'Frame evaluation and panel deferral', path: ledger + '#paired-frame-completion-goal'},
    ];
  if (model === 'eoere-leg-header-frame-development')
    return [
      {label: 'Preserved 96-axis member and receiver layout', path: evidence + 'leg-header-v3/receiver-holes.csv'},
      {label: 'Combined geometry and hardware receipt', path: evidence + 'leg-header-v3/geometry.json'},
      {label: '96 selected bolt stacks and spacers', path: evidence + 'leg-header-v3/hardware-selection.csv'},
      {label: '32 retained enclosed-passage datums', path: evidence + 'enclosed-passages-v1/passage-datums.csv'},
      {label: 'Own calculations and remaining holds', path: ledger + '#single-bolt-leg-joint-review'},
      {label: 'Active successor · separate shop packet', path: current + 'builder-plan.md'},
    ];
  if (model === 'eoere-enclosed-passages-frame-development')
    return [
      {label: 'Active successor builder plan · separate geometry', path: current + 'builder-plan.md'},
      {label: 'Current member and receiver layout', path: current + 'builder-layout.md'},
      {label: '32 enclosed-passage datums', path: evidence + 'enclosed-passages-v1/passage-datums.csv'},
      {label: 'Enclosed-passage geometry receipt', path: evidence + 'enclosed-passages-v1/geometry.json'},
      {label: 'Passage section diagram', path: current + 'enclosed-passage-study.svg'},
      {label: 'Six preceding cases · extra grid off · earlier geometry', path: evidence + 'selected-hardware-v1/current-response-v1/result.json'},
    ];
  if (['eoere-narrow-channels-frame-development', 'eoere-narrow-channels-grid-development'].includes(model))
    return [
      {label: 'Active successor builder plan · separate geometry', path: current + 'builder-plan.md'},
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
