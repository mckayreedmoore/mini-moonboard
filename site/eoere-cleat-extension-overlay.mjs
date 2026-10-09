// Two extended cleats shared by the frozen adjusted-base and optional-grid views.
import {meshGeometry, sha256, decodeTypedArray} from './wood-joints-overlay.mjs';
import {loadAdjustedFrameScene, load2026AdjustmentsScene} from './eoere-2026-adjustments-overlay.mjs';

const SHA = /^[0-9a-f]{64}$/;
const REVISION = 'eoere-base-side-edge-cleats-v1';
const NAMES = ['eoere_cleat_left', 'eoere_cleat_right'];
const PARENTS = Object.freeze({
  base: Object.freeze({url: 'eoere-adjusted-base-v3-scene.json.gz',
    sha256: 'd77b9923b7d0df6b3416b2938b2d249a5406a9174fe98fba5118c341bc3df947',
    decoded_sha256: 'dfeccf743c1e18f8fc2cadd81dd975c94d3057a88923155f3b2a7166f5ae40b7',
    layout_sha256: '5e0f05ea39347edcd89e088ab0cd478976b9a7ae9dabcc78c1b92e24d1f01aa7'}),
  extra: Object.freeze({url: 'eoere-2026-adjustments-v3-scene.json.gz',
    sha256: '8682bf9a81c0bf8e7ffb23c3f6725adc6d3c9bd4728b00e50edb696ca3305d1d',
    decoded_sha256: '914dd1def234c0657b136f6d2aba0b78456f7ee4a7b8b8df449908f0f6b501d6',
    layout_sha256: '5dfa03b785715c92717725400e73bf41b00a58160595ddf6b61b61c3b31f6134'})
});
function require(ok, message) { if (!ok) throw new Error(`Extended cleats: ${message}`); }

export function validateCleatExtension(data, layoutSha256) {
  require(data?.schema === 'eoere_cleat_top_extension_patch/v1' &&
    data.candidate === 'compact-floor-flush-eoere-bolted-development' &&
    data.revision === REVISION && data.status === 'REVISE_UNEVALUATED_GEOMETRY',
    'distinct geometry identity required');
  require(SHA.test(layoutSha256 || '') && data.layout_report?.sha256 === layoutSha256 &&
    data.layout_report.path === 'docs/wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/occupied-extended-cleats-v1.json',
    'geometry binding required');
  require(data.mechanics_ready === false && data.analysis_pass_transferred === false &&
    data.only_two_cleat_bodies_changed === true && data.base_and_extra_harness_retained === true &&
    data.release && Object.keys(data.release).length >= 6 && Object.values(data.release).every(value => value === false),
    'geometry-only extension and unresolved release required');
  for (const [variant, binding] of Object.entries(PARENTS)) {
    require(Object.entries(binding).every(([key, value]) => data.parent_scenes?.[variant]?.[key] === value),
      `${variant} parent differs`);
    const counts = data.counts?.[variant];
    require(counts?.physical_bolt_axes === 100 && counts.screw === 66 && counts.timber === 22 &&
      counts.panel === 6 && counts.bracket === 22 && counts.bolt === 500 &&
      counts.lights === (variant === 'base' ? 132 : 252) && counts.tnuts === (variant === 'base' ? 142 : 262) &&
      counts.wire === (variant === 'base' ? 131 : 250) && counts.total_visible_parts === (variant === 'base' ? 1021 : 1380),
      `${variant} census differs`);
  }
  require(Array.isArray(data.replacements) && data.replacements.length === 2 &&
    new Set(data.replacements.map(row => row.name)).size === 2 &&
    data.replacements.every(row => NAMES.includes(row.name) && row.id === row.name && row.mesh &&
      !row.transform && !row.template_id && row.fabrication?.kind === 'timber' &&
      row.fabrication.cleat_extension_revision === REVISION), 'exactly two direct cleat meshes required');
  return data;
}

export function loadExtendedCleatBaseScene(THREE, options) { return loadScene(THREE, options, 'base'); }
export function loadExtendedCleat2026Scene(THREE, options) { return loadScene(THREE, options, 'extra'); }

async function loadScene(THREE, options, variant) {
  require(SHA.test(options.expectedSha256 || '') && SHA.test(options.decodedSha256 || ''), 'scene hashes required');
  const response = await fetch(options.url);
  require(response.ok, `scene request failed (${response.status})`);
  const encoded = await response.arrayBuffer();
  require(await sha256(encoded) === options.expectedSha256, 'compressed bytes differ');
  const decoded = await new Response(new Blob([encoded]).stream().pipeThrough(new DecompressionStream('gzip'))).arrayBuffer();
  require(await sha256(decoded) === options.decodedSha256, 'decoded bytes differ');
  const data = validateCleatExtension(JSON.parse(new TextDecoder('utf-8', {fatal: true}).decode(decoded)), options.layoutSha256);
  const topologies = new Map();
  for (const [digest, row] of Object.entries(data.triangle_topologies)) {
    require(SHA.test(digest) && ['uint16', 'uint32'].includes(row.triangle_component_type) &&
      Number.isInteger(row.triangle_count) && row.triangle_count > 0 && row.index_count === row.triangle_count * 3,
      'valid triangle topology required');
    const indices = decodeTypedArray(row.triangle_indices_base64, row.triangle_component_type, row.index_count);
    require(await sha256(indices.bytes) === digest, 'triangle bytes differ');
    topologies.set(digest, {...row, indices: indices.values});
  }
  const binding = PARENTS[variant];
  const parent = await (variant === 'base' ? loadAdjustedFrameScene : load2026AdjustmentsScene)(THREE, {
    ...options, url: binding.url, expectedSha256: binding.sha256,
    decodedSha256: binding.decoded_sha256, layoutSha256: binding.layout_sha256});
  const allocated = new Set();
  try {
    const old = new Map(parent.parts.map(part => [part.name, part]));
    const replacements = new Map();
    for (const row of data.replacements) {
      require(old.get(row.name)?.fabrication.kind === 'timber', 'parent cleat missing');
      const geometry = meshGeometry(THREE, row.mesh, topologies); allocated.add(geometry);
      geometry.computeBoundingBox();
      const dimensions = ['x', 'y', 'z'].map(axis => geometry.boundingBox.max[axis] - geometry.boundingBox.min[axis]);
      require(dimensions.every(value => Number.isFinite(value) && value > 0), 'finite cleat extent required');
      const part = {...old.get(row.name), name: row.name, geometry,
        fabrication: {...old.get(row.name).fabrication, ...row.fabrication, dimensions_mm: dimensions,
          layer: 'eoere_cleat_extension', display_class: 'eoere_cleat_extension'}};
      delete part.path;
      replacements.set(row.name, part);
    }
    const parts = parent.parts.map(part => replacements.get(part.name) || part);
    require(parts.length === data.counts[variant].total_visible_parts && new Set(parts.map(part => part.name)).size === parts.length,
      'visible census differs');
    for (const name of NAMES) old.get(name).geometry?.dispose();
    return {...parent, parts,
      design: {...parent.design, key: variant === 'base' ? 'eoere-extended-cleat-frame-development' : 'eoere-extended-cleat-2026-development',
        qualified_for_design: false},
      meta: {...parent.meta, schema: data.schema, revision: REVISION, source_sha256: options.expectedSha256,
        decoded_sha256: options.decodedSha256, layout_sha256: options.layoutSha256, cleat_extension_variant: variant,
        unchanged_visible_parts_reused: parts.length - 2,
        analysis_pass_transferred: false, complete_joint_acceptance: false, physical_release: false, planning_mass_kg: null}};
  } catch (error) {
    for (const geometry of allocated) geometry.dispose();
    for (const part of parent.parts) part.geometry?.dispose();
    throw error;
  }
}
