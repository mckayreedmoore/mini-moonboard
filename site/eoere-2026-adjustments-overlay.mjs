// Adjusted base frame plus a separate unofficial, provisional midpoint layer.
import {meshGeometry, sha256, decodeTypedArray} from './wood-joints-overlay.mjs';
import {loadEoereAlignedWireGzipScene} from './eoere-aligned-wire-gzip-overlay.mjs';

const SHA = /^[0-9a-f]{64}$/;
const PARENT = Object.freeze({url: 'eoere-aligned-wire-scene.json.gz',
  sha256: 'dbb6c2cdf65b4473b71a38faa233dd7c6f43bb02bb07ad6a702943c343947ee4',
  decoded_sha256: '367ddf67b376597e9ca906bb1faa904cbbfa16c98ddc86c879548a6eff637573',
  layout_sha256: '2b31d82a41cd6eb1c80e3ed84b2d0cae428fdc575b1c8c6fa27d7c3e6f0276c5'});
const ADJUSTED_PARENT = Object.freeze({url: 'eoere-adjusted-base-v3-scene.json.gz',
  sha256: 'd77b9923b7d0df6b3416b2938b2d249a5406a9174fe98fba5118c341bc3df947',
  decoded_sha256: 'dfeccf743c1e18f8fc2cadd81dd975c94d3057a88923155f3b2a7166f5ae40b7',
  layout_sha256: '5e0f05ea39347edcd89e088ab0cd478976b9a7ae9dabcc78c1b92e24d1f01aa7'});
function require(ok, message) { if (!ok) throw new Error(`New 2026 adjustments: ${message}`); }

export function validate2026Adjustments(data, layoutSha256, base = false) {
  require(data?.schema === (base ? 'eoere_adjusted_base_patch/v1' : 'eoere_2026_adjustments_patch/v1') &&
    data.candidate === 'compact-floor-flush-eoere-bolted-development' &&
    data.revision === (base ? 'eoere-midpoint-ready-frame-v3' : 'eoere-2026-horizontal-midpoint-grid-v3') &&
    data.status === 'REVISE_UNEVALUATED_GEOMETRY', 'distinct geometry identity required');
  require(data.mechanics_ready === false && data.principal_move_adopted === true &&
    data.design?.key === (base ? 'eoere-adjusted-frame-development' : 'eoere-new-2026-adjustments') && data.design.qualified_for_design === false &&
    data.release && Object.values(data.release).length >= 6 && Object.values(data.release).every(value => value === false),
    'adjusted base and unresolved release required');
  require(Object.entries(base ? PARENT : ADJUSTED_PARENT).every(([key, value]) => data.parent_scene?.[key] === value) &&
    SHA.test(layoutSha256 || '') && data.layout_report?.sha256 === layoutSha256 &&
    data.layout_report.path === `docs/wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/${base ? 'occupied-adjusted-base-v3' : 'occupied-2026-adjustments-v3'}.json`,
    'parent and geometry bindings required');
  require(data.counts?.physical_bolt_axes === 100 && data.counts.screw === 66 &&
    data.counts.lights === (base ? 132 : 252) && data.counts.tnuts === (base ? 142 : 262) && data.counts.wire === (base ? 131 : 250) &&
    data.counts.total_visible_parts === (base ? 1021 : 1380), 'complete component census required');
  require(Array.isArray(data.replacements) && data.replacements.every(row => row.mesh && !row.transform),
    'source-bound replacement meshes required');
  if (base) {
    require(data.replacements.length === 136 && [['timber', 7], ['panel', 3], ['bracket', 6], ['bolt', 110], ['screw', 10]]
      .every(([kind, count]) => data.replacements.filter(row => row.fabrication?.kind === kind).length === count) &&
      data.additions?.length === 0 && data.templates?.length === 0, 'coordinated base inventory required');
  } else {
    require(data.unofficial_2026_positions === true && data.replacements.filter(row => row.fabrication?.kind === 'panel').length === 4 &&
      data.replacements.every(row => ['panel', 'timber', 'wire'].includes(row.fabrication?.kind)) &&
      data.replacements.filter(row => row.fabrication?.kind === 'wire').length === 10, 'unofficial machined panel layer required');
    require(Array.isArray(data.additions) && data.additions.length === 359 &&
      ['tnut', 'light', 'wire'].every(kind => data.additions.filter(row => row.fabrication?.kind === kind).length ===
        (kind === 'wire' ? 119 : 120)) && data.templates?.length === 2,
      '120 T-nuts, 120 lights and 119 separate links required');
  }
  const rows = [...data.replacements, ...data.additions];
  require(new Set(rows.map(row => row.name)).size === rows.length && rows.every(row =>
    row.id === row.name && row.fabrication.adjustment_revision === data.revision &&
    (row.mesh || (data.templates.some(t => t.id === row.template_id) &&
      Array.isArray(row.transform) && row.transform.length === 16 && row.transform.every(Number.isFinite)))),
    'unique actual meshes or source-bound template instances required');
  return data;
}

export function validateAdjustedBase(data, layoutSha256) { return validate2026Adjustments(data, layoutSha256, true); }
export function loadAdjustedFrameScene(THREE, options) { return loadScene(THREE, options, true); }
export function load2026AdjustmentsScene(THREE, options) { return loadScene(THREE, options, false); }

async function loadScene(THREE, options, base) {
  require(SHA.test(options.expectedSha256 || '') && SHA.test(options.decodedSha256 || ''), 'asset hashes required');
  const response = await fetch(options.url);
  require(response.ok, `scene request failed (${response.status})`);
  const encoded = await response.arrayBuffer();
  require(await sha256(encoded) === options.expectedSha256, 'compressed bytes differ');
  const decoded = await new Response(new Blob([encoded]).stream().pipeThrough(new DecompressionStream('gzip'))).arrayBuffer();
  require(await sha256(decoded) === options.decodedSha256, 'decoded bytes differ');
  const data = validate2026Adjustments(JSON.parse(new TextDecoder('utf-8', {fatal: true}).decode(decoded)), options.layoutSha256, base);
  const topologies = new Map();
  for (const [digest, row] of Object.entries(data.triangle_topologies)) {
    require(SHA.test(digest) && ['uint16', 'uint32'].includes(row.triangle_component_type) &&
      Number.isInteger(row.triangle_count) && row.triangle_count > 0 && row.index_count === row.triangle_count * 3,
      'valid triangle topology required');
    const decoded = decodeTypedArray(row.triangle_indices_base64, row.triangle_component_type, row.index_count);
    require(await sha256(decoded.bytes) === digest, 'triangle bytes differ');
    topologies.set(digest, {...row, indices: decoded.values});
  }
  const binding = base ? PARENT : ADJUSTED_PARENT;
  const parent = await (base ? loadEoereAlignedWireGzipScene : loadAdjustedFrameScene)(THREE, {...options, url: binding.url,
    expectedSha256: binding.sha256, decodedSha256: binding.decoded_sha256, layoutSha256: binding.layout_sha256});
  const allocated = new Set(), templates = new Map();
  try {
    for (const row of data.templates) {
      const geometry = meshGeometry(THREE, row.mesh, topologies);
      templates.set(row.id, geometry); allocated.add(geometry);
    }
    const old = new Map(parent.parts.map(row => [row.name, row]));
    const replacements = new Map();
    const render = row => {
      const geometry = row.template_id ? templates.get(row.template_id).clone() : meshGeometry(THREE, row.mesh, topologies);
      allocated.add(geometry);
      if (row.template_id) geometry.applyMatrix4(new THREE.Matrix4().fromArray(row.transform));
      geometry.computeBoundingBox();
      const dimensions = ['x', 'y', 'z'].map(axis => geometry.boundingBox.max[axis] - geometry.boundingBox.min[axis]);
      require(dimensions.every(value => Number.isFinite(value) && value > 0), 'finite part extent required');
      const part = {...old.get(row.name), name: row.name, geometry,
        fabrication: {...old.get(row.name)?.fabrication, ...row.fabrication, dimensions_mm: dimensions,
          layer: 'eoere_2026_adjustments', display_class: 'eoere_2026_adjustments'}};
      delete part.path;
      return part;
    };
    for (const row of data.replacements) {
      require(old.has(row.name) && old.get(row.name).fabrication.kind === row.fabrication.kind, 'existing replacement owner missing');
      replacements.set(row.name, render(row));
    }
    for (const row of data.additions) require(!old.has(row.name), 'new part shadows preserved grid');
    const parts = [...parent.parts.map(row => replacements.get(row.name) || row), ...data.additions.map(render)];
    require(parts.length === data.counts.total_visible_parts && new Set(parts.map(row => row.name)).size === parts.length, 'complete visible inventory differs');
    for (const name of replacements.keys()) old.get(name).geometry?.dispose();
    for (const geometry of templates.values()) geometry.dispose();
    return {...parent, parts, design: {...parent.design, ...data.design},
      meta: {...parent.meta, schema: data.schema, revision: data.revision, source_sha256: options.expectedSha256,
        decoded_sha256: options.decodedSha256, layout_sha256: options.layoutSha256,
        unchanged_visible_parts_reused: 1021 - replacements.size,
        analysis_pass_transferred: false, complete_joint_acceptance: false, physical_release: false,
        planning_mass_kg: null}};
  } catch (error) {
    for (const geometry of allocated) geometry.dispose();
    for (const part of parent.parts) part.geometry?.dispose();
    throw error;
  }
}
