// Apply the selected purchase stacks to the retained timber and screw geometry.
import {meshGeometry, sha256, decodeTypedArray} from './wood-joints-overlay.mjs';
import {loadKickerClearanceBaseScene} from './eoere-kicker-clearance-overlay.mjs';
import {loadRightColumnScene} from './eoere-right-column-overlay.mjs';

const SHA = /^[0-9a-f]{64}$/;
const REVISION = 'eoere-selected-purchase-hardware-v1';
const KEYS = {base: 'eoere-selected-hardware-frame-development', extra: 'eoere-selected-hardware-grid-development'};
const PARENTS = {
  base: {url: 'eoere-kicker-clearance-scene.json.gz',
    sha256: '0c0acfde3d6dbcaada4ffc9789898775348d4765b87525a83c20e724f8e8aa52',
    decoded_sha256: '2827864558af2b5fe9decf559c1de618391a97fe493566996263ad8453ac4003',
    layout_sha256: '7ebee98cb777de63ecdbc32007c97967c445500d93053eb942ab775568a5fb5f'},
  extra: {url: 'eoere-right-column-scene.json.gz',
    sha256: '220e8dda8aa8a7aed1b6a85aeb8237755664931b0f3a080474d9478da3970492',
    decoded_sha256: 'f584be56983e8bafe3cd68a3a20b0b88d745964b08a6b2bf3b4eeb631f1474ec',
    layout_sha256: '3707efb8f3da016673b8a418bec4603463736a11eacec3b3ddf4730fbd451d4a'},
};
function require(ok, message) { if (!ok) throw new Error('Selected hardware: ' + message); }
function rigid(m) {
  if (!Array.isArray(m) || m.length !== 16 || !m.every(Number.isFinite) ||
    m[3] !== 0 || m[7] !== 0 || m[11] !== 0 || m[15] !== 1) return false;
  const c = [m.slice(0, 3), m.slice(4, 7), m.slice(8, 11)];
  const dot = (a, b) => a.reduce((s, v, i) => s + v * b[i], 0);
  const cross = [c[0][1] * c[1][2] - c[0][2] * c[1][1],
    c[0][2] * c[1][0] - c[0][0] * c[1][2], c[0][0] * c[1][1] - c[0][1] * c[1][0]];
  return c.every((a, i) => c.every((b, j) => Math.abs(dot(a, b) - Number(i === j)) < 1e-10)) &&
    Math.abs(dot(cross, c[2]) - 1) < 1e-10;
}

export function validateSelectedHardware(data, layoutSha256) {
  require(data?.schema === 'eoere_selected_hardware_patch/v1' && data.revision === REVISION &&
    data.candidate === 'compact-floor-flush-eoere-bolted-development' &&
    data.status === 'REVISE_UNEVALUATED_HARDWARE_GEOMETRY', 'geometry identity required');
  require(SHA.test(layoutSha256 || '') && data.layout_report?.sha256 === layoutSha256 &&
    data.layout_report.path === 'docs/wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/occupied-selected-hardware-v1.json',
    'geometry binding required');
  require(Object.entries(PARENTS).every(([variant, parent]) => Object.entries(parent).every(([key, value]) =>
    data.parents?.[variant]?.[key] === value) && data.keys?.[variant] === KEYS[variant]), 'retained parents required');
  require(data.mechanics_ready === false && data.analysis_pass_transferred === false &&
    Object.keys(data.release || {}).length >= 6 && Object.values(data.release).every(value => value === false),
    'unresolved mechanics and physical release required');
  require(Object.entries({base: 1029, extra: 1424, physical_bolt_axes: 100, longer_shafts: 32,
    translated_nuts: 8, added_spacers: 8, timbers: 22, panels: 6, angles: 22, Hillman_screws: 66})
    .every(([key, count]) => data.counts?.[key] === count), 'complete census required');
  require(Array.isArray(data.selected_stacks) && data.selected_stacks.length === 100 &&
    new Set(data.selected_stacks.map(row => row.axis_id)).size === 100, '100 unique stacks required');
  const positive = ['selected_underhead_length_mm', 'minimum_length_mm', 'minimum_body_mm',
    'maximum_grip_gaging_mm', 'minimum_body_to_nominated_target_margin_mm',
    'minimum_nut_seating_margin_mm', 'minimum_two_pitch_margin_mm'];
  require(data.selected_stacks.every(row => typeof row.axis_id === 'string' &&
    [9.525, 12.7].includes(row.selected_diameter_mm) && positive.every(key => Number.isFinite(row[key]) && row[key] > 0) &&
    Number.isFinite(row.selected_tip_delta_mm) && row.selected_tip_delta_mm >= 0 &&
    [0, 12.7].includes(row.nut_side_spacer_mm) &&
    row.selected_bolt_grade === 'SAE J429 Grade 5; zinc; partially threaded full body'), 'selected stack windows required');
  const longer = data.selected_stacks.filter(row => row.selected_tip_delta_mm > 0);
  const spaced = data.selected_stacks.filter(row => row.nut_side_spacer_mm === 12.7);
  require(longer.length === 32 && spaced.length === 8, '32 longer bolts and eight spacers required');
  require(Array.isArray(data.templates) && data.templates.length === 6 &&
    new Set(data.templates.map(row => row.id)).size === 6 &&
    data.templates.every(row => /^(selected_shaft_[1-5]|selected_spacer)$/.test(row.id) &&
      row.mesh && SHA.test(row.source_brep_sha256 || '')), 'shared source-bound templates required');
  const checkRows = (rows, axes, role) => Array.isArray(rows) && rows.length === axes.length &&
    axes.every(axis => rows.some(row => row.name === axis.axis_id + '_' + role)) &&
    rows.every(row => row.id === row.name && row.fabrication?.kind === 'bolt' &&
      row.fabrication.hardware_role === role && row.fabrication.selected_hardware_revision === REVISION &&
      row.name === row.fabrication.connection_name + '_' + role && SHA.test(row.source_brep_sha256 || '') &&
      (role === 'spacer' ? row.template_id === 'selected_spacer' : /^selected_shaft_[1-5]$/.test(row.template_id)) &&
      data.templates.some(template => template.id === row.template_id) && rigid(row.transform));
  require(checkRows(data.replacements, longer, 'shaft') && checkRows(data.additions, spaced, 'spacer'),
    'exact longer shaft and spacer instances required');
  require(Array.isArray(data.translations) && data.translations.length === 8 &&
    spaced.every(axis => data.translations.some(row => row.name === axis.axis_id + '_nut')) &&
    data.translations.every(row => row.fabrication?.kind === 'bolt' && row.fabrication.hardware_role === 'nut' &&
      row.fabrication.selected_hardware_revision === REVISION && row.name === row.fabrication.connection_name + '_nut' &&
      SHA.test(row.source_brep_sha256 || '') && Array.isArray(row.translation_xyz_mm) &&
      row.translation_xyz_mm.length === 3 && row.translation_xyz_mm.every(Number.isFinite) &&
      Math.abs(Math.hypot(...row.translation_xyz_mm) - 12.7) < 1e-10), 'eight nut translations required');
  require(new Set([...data.replacements, ...data.additions, ...data.translations].map(row => row.name)).size === 48,
    'unique changed parts required');
  return data;
}

async function loadScene(THREE, options, variant) {
  require(SHA.test(options.expectedSha256 || '') && SHA.test(options.decodedSha256 || ''), 'scene hashes required');
  const response = await fetch(options.url);
  require(response.ok, 'scene request failed (' + response.status + ')');
  const encoded = await response.arrayBuffer();
  require(await sha256(encoded) === options.expectedSha256, 'compressed bytes differ');
  const decoded = await new Response(new Blob([encoded]).stream().pipeThrough(new DecompressionStream('gzip'))).arrayBuffer();
  require(await sha256(decoded) === options.decodedSha256, 'decoded bytes differ');
  const data = validateSelectedHardware(JSON.parse(new TextDecoder('utf-8', {fatal: true}).decode(decoded)), options.layoutSha256);
  const topologies = new Map();
  for (const [digest, row] of Object.entries(data.triangle_topologies)) {
    require(SHA.test(digest) && ['uint16', 'uint32'].includes(row.triangle_component_type) &&
      Number.isInteger(row.triangle_count) && row.triangle_count > 0 && row.index_count === row.triangle_count * 3,
      'valid topology required');
    const indices = decodeTypedArray(row.triangle_indices_base64, row.triangle_component_type, row.index_count);
    require(await sha256(indices.bytes) === digest, 'triangle bytes differ');
    topologies.set(digest, {...row, indices: indices.values});
  }
  const binding = PARENTS[variant];
  const parentLoader = variant === 'base' ? loadKickerClearanceBaseScene : loadRightColumnScene;
  const parent = await parentLoader(THREE, {...options, url: binding.url,
    expectedSha256: binding.sha256, decodedSha256: binding.decoded_sha256, layoutSha256: binding.layout_sha256});
  const allocated = new Set(), templates = new Map();
  try {
    require(parent.parts.length === data.counts[variant] - 8, 'parent census differs');
    const old = new Map(parent.parts.map(part => [part.name, part])), replacements = new Map();
    const render = row => {
      const previous = old.get(row.name) || old.get(row.fabrication.connection_name + '_nut');
      require(previous?.fabrication.kind === 'bolt', 'retained hardware missing: ' + row.name);
      const geometry = row.template_id ? templates.get(row.template_id).clone() : previous.geometry.clone();
      allocated.add(geometry);
      if (row.template_id) geometry.applyMatrix4(new THREE.Matrix4().fromArray(row.transform));
      else geometry.translate(...row.translation_xyz_mm);
      geometry.computeBoundingBox();
      const dimensions = ['x', 'y', 'z'].map(axis => geometry.boundingBox.max[axis] - geometry.boundingBox.min[axis]);
      require(dimensions.every(value => Number.isFinite(value) && value > 0), 'finite part extent required');
      const part = {...previous, name: row.name, geometry,
        fabrication: {...previous.fabrication, ...row.fabrication, dimensions_mm: dimensions}};
      delete part.path;
      return part;
    };
    for (const row of data.templates) {
      const geometry = meshGeometry(THREE, row.mesh, topologies);
      allocated.add(geometry); templates.set(row.id, geometry);
    }
    for (const row of [...data.replacements, ...data.translations]) {
      require(old.has(row.name), 'replacement missing: ' + row.name);
      replacements.set(row.name, render(row));
    }
    for (const row of data.additions) require(!old.has(row.name), 'spacer shadows existing part');
    const selected = new Map(data.selected_stacks.map(row => [row.axis_id, row]));
    const parts = [...parent.parts.map(part => replacements.get(part.name) || part), ...data.additions.map(render)]
      .map(part => {
        if (part.fabrication.kind !== 'bolt') return part;
        const row = selected.get(part.fabrication.connection_name);
        require(row, 'unmapped bolt part: ' + part.name);
        return {...part, fabrication: {...part.fabrication, selected_hardware_revision: REVISION,
          description: part.fabrication.hardware_role === 'spacer' ?
            'Factory steel spacer; nominal 12.7 mm long, 19.05 mm OD, 10.31875 mm ID; delivered part unverified' :
            'Selected Grade 5 partial-thread bolt stack; nominal underhead length ' + row.selected_underhead_length_mm + ' mm; delivered parts unverified',
          stack_roles: ['shaft', 'head', 'head_washer', 'nut_washer', ...(row.nut_side_spacer_mm ? ['spacer'] : []), 'nut'],
          selected_underhead_length_mm: row.selected_underhead_length_mm,
          selected_bolt_grade: row.selected_bolt_grade, minimum_body_mm: row.minimum_body_mm,
          maximum_grip_gaging_mm: row.maximum_grip_gaging_mm, nut_side_spacer_mm: row.nut_side_spacer_mm,
          delivered_part_verified: false}};
      });
    require(parts.length === data.counts[variant] && new Set(parts.map(part => part.name)).size === parts.length &&
      parts.filter(part => part.fabrication.kind === 'bolt').length === 508, 'visible census differs');
    const bounds = parent.bounds_mm.map(point => [...point]);
    for (const part of parts.filter(part => replacements.has(part.name) || part.fabrication.hardware_role === 'spacer')) {
      const box = part.geometry.boundingBox;
      for (const [i, axis] of ['x', 'y', 'z'].entries()) {
        bounds[0][i] = Math.min(bounds[0][i], box.min[axis]);
        bounds[1][i] = Math.max(bounds[1][i], box.max[axis]);
      }
    }
    for (const name of replacements.keys()) old.get(name).geometry.dispose();
    for (const geometry of templates.values()) geometry.dispose();
    return {...parent, parts, bounds_mm: bounds, design: {...parent.design, key: KEYS[variant], qualified_for_design: false},
      meta: {...parent.meta, schema: data.schema, revision: REVISION, source_sha256: options.expectedSha256,
        decoded_sha256: options.decodedSha256, layout_sha256: options.layoutSha256,
        hardware_model_updated: true, unchanged_geometries_reused: parent.parts.length - 40,
        bounds_scope: 'Retained parent display envelope expanded for selected hardware',
        selected_bolt_stacks: 100, added_spacers: 8, optional_grid_unofficial: variant === 'extra',
        analysis_pass_transferred: false, complete_joint_acceptance: false, physical_release: false, planning_mass_kg: null}};
  } catch (error) {
    for (const geometry of allocated) geometry.dispose();
    for (const part of parent.parts) part.geometry?.dispose();
    throw error;
  }
}
export const loadSelectedHardwareBaseScene = (THREE, options) => loadScene(THREE, options, 'base');
export const loadSelectedHardwareGridScene = (THREE, options) => loadScene(THREE, options, 'extra');
