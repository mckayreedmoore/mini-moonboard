// Optional expanded grid with one column 100 mm right of K.
import {meshGeometry, sha256, decodeTypedArray} from './wood-joints-overlay.mjs';
import {loadKickerClearance2026Scene} from './eoere-kicker-clearance-overlay.mjs';

const SHA = /^[0-9a-f]{64}$/;
const REVISION = 'eoere-expanded-right-column-v1';
const KEY = 'eoere-expanded-right-column-development';
const CHANGED = new Map([
  ['main_lower_right', 'panel'], ['main_upper_right', 'panel'],
  ['base_rail_bottom_right', 'timber'], ['base_rail_service_lower_right', 'timber'],
  ['base_rail_service_upper_right', 'timber'],
]);
const PARENT = Object.freeze({url: 'eoere-kicker-clearance-scene.json.gz',
  sha256: '0c0acfde3d6dbcaada4ffc9789898775348d4765b87525a83c20e724f8e8aa52',
  decoded_sha256: '2827864558af2b5fe9decf559c1de618391a97fe493566996263ad8453ac4003',
  layout_sha256: '7ebee98cb777de63ecdbc32007c97967c445500d93053eb942ab775568a5fb5f'});
function require(ok, message) { if (!ok) throw new Error(`Expanded right column: ${message}`); }

export function validateRightColumn(data, layoutSha256) {
  require(data?.schema === 'eoere_right_column_patch/v1' && data.revision === REVISION &&
    data.candidate === 'compact-floor-flush-eoere-bolted-development' &&
    data.status === 'REVISE_UNEVALUATED_GEOMETRY', 'geometry identity required');
  require(Object.entries(PARENT).every(([key, value]) => data.parent_scene?.[key] === value) &&
    SHA.test(layoutSha256 || '') && data.layout_report?.sha256 === layoutSha256 &&
    data.layout_report.path === 'docs/wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/occupied-right-column-v1.json',
    'parent and geometry bindings required');
  require(data.optional_grid_unofficial === true && data.base_geometry_unchanged === true &&
    data.mechanics_ready === false && data.analysis_pass_transferred === false &&
    Object.keys(data.release || {}).length >= 6 && Object.values(data.release).every(value => value === false),
    'unofficial geometry and unresolved release required');
  require(Object.entries({timber: 22, panel: 6, bracket: 22, bolt: 500, screw: 66,
    physical_bolt_axes: 100, tnuts: 274, lights: 264, wire: 262, total_visible_parts: 1416})
    .every(([kind, count]) => data.counts?.[kind] === count), 'complete census required');
  require(Array.isArray(data.grid) && data.grid.length === 12 && data.grid.every((row, i) =>
    row.id === `Kplus${i + 1}` && row.row === i + 1 && row.column === 'Kplus' &&
    [row.tnut_x_s_mm, row.LED_x_s_mm].every(point => Array.isArray(point) && point.length === 2 &&
      point.every(Number.isFinite) && point[0] === 2300)), 'twelve X2300 positions required');
  require(Array.isArray(data.replacements) && data.replacements.length === 5 &&
    [...CHANGED.keys()].every(name => data.replacements.some(row => row.name === name)) &&
    data.replacements.every(row => row.mesh && !row.transform && !row.template_id &&
      row.fabrication?.kind === CHANGED.get(row.name)), 'two panels and three channel rails required');
  require(Array.isArray(data.templates) && data.templates.length === 2 &&
    ['right_tnut', 'right_light'].every(id => data.templates.some(row => row.id === id && row.mesh)),
    'shared T-nut and LED templates required');
  require(Array.isArray(data.additions) && data.additions.length === 36 && ['tnut', 'light', 'wire'].every(kind =>
    data.additions.filter(row => row.fabrication?.kind === kind).length === 12), 'twelve T-nuts, LEDs and links required');
  const rows = [...data.replacements, ...data.additions];
  require(new Set(rows.map(row => row.name)).size === 41 && rows.every(row => row.id === row.name &&
    row.fabrication.right_column_revision === REVISION && SHA.test(row.source_brep_sha256 || '') === Boolean(row.mesh) &&
    (row.mesh ? !row.template_id && !row.transform : data.templates.some(t => t.id === row.template_id) &&
      Array.isArray(row.transform) && row.transform.length === 16 && row.transform.every(Number.isFinite))),
    'unique source meshes or template instances required');
  return data;
}

export async function loadRightColumnScene(THREE, options) {
  require(SHA.test(options.expectedSha256 || '') && SHA.test(options.decodedSha256 || ''), 'scene hashes required');
  const response = await fetch(options.url);
  require(response.ok, `scene request failed (${response.status})`);
  const encoded = await response.arrayBuffer();
  require(await sha256(encoded) === options.expectedSha256, 'compressed bytes differ');
  const decoded = await new Response(new Blob([encoded]).stream().pipeThrough(new DecompressionStream('gzip'))).arrayBuffer();
  require(await sha256(decoded) === options.decodedSha256, 'decoded bytes differ');
  const data = validateRightColumn(JSON.parse(new TextDecoder('utf-8', {fatal: true}).decode(decoded)), options.layoutSha256);
  const topologies = new Map();
  for (const [digest, row] of Object.entries(data.triangle_topologies)) {
    require(SHA.test(digest) && ['uint16', 'uint32'].includes(row.triangle_component_type) &&
      Number.isInteger(row.triangle_count) && row.triangle_count > 0 && row.index_count === row.triangle_count * 3,
      'valid topology required');
    const indices = decodeTypedArray(row.triangle_indices_base64, row.triangle_component_type, row.index_count);
    require(await sha256(indices.bytes) === digest, 'triangle bytes differ');
    topologies.set(digest, {...row, indices: indices.values});
  }
  const parent = await loadKickerClearance2026Scene(THREE, {...options, url: PARENT.url,
    expectedSha256: PARENT.sha256, decodedSha256: PARENT.decoded_sha256, layoutSha256: PARENT.layout_sha256});
  const allocated = new Set(), templates = new Map();
  try {
    for (const row of data.templates) {
      const geometry = meshGeometry(THREE, row.mesh, topologies);
      templates.set(row.id, geometry); allocated.add(geometry);
    }
    const old = new Map(parent.parts.map(part => [part.name, part])), replacements = new Map();
    const render = row => {
      const geometry = row.template_id ? templates.get(row.template_id).clone() : meshGeometry(THREE, row.mesh, topologies);
      allocated.add(geometry);
      if (row.template_id) geometry.applyMatrix4(new THREE.Matrix4().fromArray(row.transform));
      geometry.computeBoundingBox();
      const dimensions = ['x', 'y', 'z'].map(axis => geometry.boundingBox.max[axis] - geometry.boundingBox.min[axis]);
      require(dimensions.every(value => Number.isFinite(value) && value > 0), 'finite part extent required');
      const part = {...old.get(row.name), name: row.name, geometry,
        fabrication: {...old.get(row.name)?.fabrication, ...row.fabrication, dimensions_mm: dimensions,
          layer: 'eoere_right_column', display_class: 'eoere_right_column'}};
      delete part.path;
      return part;
    };
    for (const row of data.replacements) {
      require(old.get(row.name)?.fabrication.kind === row.fabrication.kind, `parent part missing: ${row.name}`);
      replacements.set(row.name, render(row));
    }
    for (const row of data.additions) require(!old.has(row.name), 'addition shadows existing grid');
    const parts = [...parent.parts.map(part => replacements.get(part.name) || part), ...data.additions.map(render)];
    require(parts.length === 1416 && new Set(parts.map(part => part.name)).size === parts.length, 'visible census differs');
    for (const name of replacements.keys()) old.get(name).geometry?.dispose();
    for (const geometry of templates.values()) geometry.dispose();
    return {...parent, parts, design: {...parent.design, key: KEY, qualified_for_design: false},
      meta: {...parent.meta, schema: data.schema, revision: REVISION, source_sha256: options.expectedSha256,
        decoded_sha256: options.decodedSha256, layout_sha256: options.layoutSha256,
        unchanged_visible_parts_reused: 1375, main_face_positions: 264, kicker_positions: 10,
        analysis_pass_transferred: false, complete_joint_acceptance: false, physical_release: false, planning_mass_kg: null}};
  } catch (error) {
    for (const geometry of allocated) geometry.dispose();
    for (const part of parent.parts) part.geometry?.dispose();
    throw error;
  }
}
