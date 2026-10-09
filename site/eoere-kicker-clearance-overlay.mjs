// Two mirrored kicker holes/screws raised 20 mm on the uniform-channel frame.
import {meshGeometry, sha256, decodeTypedArray} from './wood-joints-overlay.mjs';
import {loadUniformChannelBaseScene, loadUniformChannel2026Scene} from './eoere-uniform-channels-overlay.mjs';

const SHA = /^[0-9a-f]{64}$/;
const REVISION = 'eoere-raised-kicker-screws-v1';
const NAMES = ['kicker_left', 'kicker_right', 'fastener_round_kicker_left_rim_2', 'fastener_round_kicker_right_rim_2'];
function require(ok, message) { if (!ok) throw new Error(`Kicker clearance: ${message}`); }

export function validateKickerClearance(data, layoutSha256) {
  require(data?.schema === 'eoere_kicker_screw_clearance_patch/v1' &&
    data.candidate === 'compact-floor-flush-eoere-bolted-development' &&
    data.revision === REVISION && data.status === 'REVISE_UNEVALUATED_GEOMETRY', 'geometry identity required');
  require(SHA.test(layoutSha256 || '') && data.layout_report?.sha256 === layoutSha256 &&
    data.layout_report.path === 'docs/wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/occupied-kicker-clearance-v1.json', 'geometry binding required');
  require(data.parent_scene?.url === 'eoere-uniform-channels-scene.json.gz' &&
    ['sha256', 'decoded_sha256', 'layout_sha256'].every(key => SHA.test(data.parent_scene[key] || '')), 'uniform-channel parent required');
  require(data.mechanics_ready === false && data.analysis_pass_transferred === false &&
    data.release && Object.keys(data.release).length >= 6 && Object.values(data.release).every(value => value === false), 'unresolved release required');
  for (const variant of ['base', 'extra']) {
    const count = data.counts?.[variant];
    require(count?.physical_bolt_axes === 100 && count.screw === 66 && count.timber === 22 && count.panel === 6 &&
      count.bracket === 22 && count.bolt === 500 && count.total_visible_parts === (variant === 'base' ? 1021 : 1380) &&
      count.lights === (variant === 'base' ? 132 : 252) && count.tnuts === (variant === 'base' ? 142 : 262) &&
      count.wire === (variant === 'base' ? 131 : 250), `${variant} census differs`);
  }
  require(Array.isArray(data.replacements) && data.replacements.length === 4 &&
    new Set(data.replacements.map(row => row.name)).size === 4 && data.replacements.every(row =>
      NAMES.includes(row.name) && row.id === row.name && row.mesh && !row.transform && !row.template_id &&
      row.fabrication?.kind === (row.name.startsWith('fastener_') ? 'screw' : 'panel') &&
      row.fabrication.kicker_clearance_revision === REVISION), 'exactly two panels and two screws required');
  const moves = data.moved_screw_axes;
  require(Array.isArray(moves) && moves.length === 2 && new Set(moves.map(row => row.axis_id)).size === 2 &&
    moves.every(row => ['round_kicker_left_rim_2', 'round_kicker_right_rim_2'].includes(row.axis_id) &&
      row.old_origin_xyz_mm?.length === 3 && row.new_origin_xyz_mm?.length === 3 &&
      row.old_origin_xyz_mm.every(Number.isFinite) && row.new_origin_xyz_mm.every(Number.isFinite) &&
      row.old_origin_xyz_mm[2] === 192 && row.new_origin_xyz_mm[2] === 212 &&
      row.old_origin_xyz_mm.slice(0, 2).every((value, i) => value === row.new_origin_xyz_mm[i]) &&
      JSON.stringify(row.translation_xyz_mm) === '[0,0,20]'), 'exact two upward moves required');
  return data;
}

export function loadKickerClearanceBaseScene(THREE, options) { return loadScene(THREE, options, 'base'); }
export function loadKickerClearance2026Scene(THREE, options) { return loadScene(THREE, options, 'extra'); }

async function loadScene(THREE, options, variant) {
  require(SHA.test(options.expectedSha256 || '') && SHA.test(options.decodedSha256 || ''), 'scene hashes required');
  const response = await fetch(options.url);
  require(response.ok, `scene request failed (${response.status})`);
  const encoded = await response.arrayBuffer();
  require(await sha256(encoded) === options.expectedSha256, 'compressed bytes differ');
  const decoded = await new Response(new Blob([encoded]).stream().pipeThrough(new DecompressionStream('gzip'))).arrayBuffer();
  require(await sha256(decoded) === options.decodedSha256, 'decoded bytes differ');
  const data = validateKickerClearance(JSON.parse(new TextDecoder('utf-8', {fatal: true}).decode(decoded)), options.layoutSha256);
  const topologies = new Map();
  for (const [digest, row] of Object.entries(data.triangle_topologies)) {
    require(SHA.test(digest) && ['uint16', 'uint32'].includes(row.triangle_component_type) &&
      Number.isInteger(row.triangle_count) && row.triangle_count > 0 && row.index_count === row.triangle_count * 3, 'valid topology required');
    const indices = decodeTypedArray(row.triangle_indices_base64, row.triangle_component_type, row.index_count);
    require(await sha256(indices.bytes) === digest, 'triangle bytes differ');
    topologies.set(digest, {...row, indices: indices.values});
  }
  const binding = data.parent_scene;
  const parent = await (variant === 'base' ? loadUniformChannelBaseScene : loadUniformChannel2026Scene)(THREE, {
    ...options, url: binding.url, expectedSha256: binding.sha256,
    decodedSha256: binding.decoded_sha256, layoutSha256: binding.layout_sha256});
  const allocated = new Set();
  try {
    const old = new Map(parent.parts.map(part => [part.name, part])), replacements = new Map();
    for (const row of data.replacements) {
      require(old.get(row.name)?.fabrication.kind === row.fabrication.kind, `parent part missing: ${row.name}`);
      const geometry = meshGeometry(THREE, row.mesh, topologies); allocated.add(geometry);
      geometry.computeBoundingBox();
      const dimensions = ['x', 'y', 'z'].map(axis => geometry.boundingBox.max[axis] - geometry.boundingBox.min[axis]);
      require(dimensions.every(value => Number.isFinite(value) && value > 0), 'finite part extent required');
      const part = {...old.get(row.name), name: row.name, geometry,
        fabrication: {...old.get(row.name).fabrication, ...row.fabrication, dimensions_mm: dimensions,
          layer: 'eoere_kicker_clearance', display_class: 'eoere_kicker_clearance'}};
      delete part.path;
      replacements.set(row.name, part);
    }
    const parts = parent.parts.map(part => replacements.get(part.name) || part);
    require(parts.length === data.counts[variant].total_visible_parts && new Set(parts.map(part => part.name)).size === parts.length, 'visible census differs');
    for (const name of NAMES) old.get(name).geometry?.dispose();
    return {...parent, parts,
      design: {...parent.design, key: variant === 'base' ? 'eoere-kicker-clearance-frame-development' : 'eoere-kicker-clearance-2026-development', qualified_for_design: false},
      meta: {...parent.meta, schema: data.schema, revision: REVISION, source_sha256: options.expectedSha256,
        decoded_sha256: options.decodedSha256, layout_sha256: options.layoutSha256,
        kicker_clearance_variant: variant, unchanged_visible_parts_reused: parts.length - 4,
        analysis_pass_transferred: false, complete_joint_acceptance: false, physical_release: false}};
  } catch (error) {
    for (const geometry of allocated) geometry.dispose();
    for (const part of parent.parts) part.geometry?.dispose();
    throw error;
  }
}
