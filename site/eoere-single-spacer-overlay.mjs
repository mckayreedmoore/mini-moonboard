import {sha256} from './wood-joints-overlay.mjs';
import {loadInwardAngleScene} from './eoere-inward-angles-overlay.mjs';

const require = (ok, message) => {if (!ok) throw new Error('Single spacers: '+message);};
const same = (a, b) => JSON.stringify(a) === JSON.stringify(b);
const AXES = ['eoere_bolt_067', 'eoere_bolt_070', 'eoere_bolt_071', 'eoere_bolt_074',
  ...['left', 'right'].flatMap(side => [1, 2].map(n => 'cleat_post_bolt_'+side+'_'+n))];
const ROLES = ['shaft', 'head', 'head_washer', 'nut_washer', 'spacer', 'nut'];
const finite = v => Array.isArray(v) && v.length === 3 && v.every(Number.isFinite);

export function validateSingleSpacers(data, layoutSha256) {
  require(data?.schema === 'eoere_single_spacer_patch/v1' && data.revision === 'eoere-single-spacer-cleat-stacks-v9' &&
    data.key === 'eoere-current-frame-development', 'revision differs');
  require(/^[a-f0-9]{64}$/.test(layoutSha256 || '') && data.layout_report?.sha256 === layoutSha256, 'receipt differs');
  require(data.parent_scene?.sha256 === '0ab99f31abce3edd855963dc0132947d01dd2f7086da2063980aca65a073369f' &&
    data.parent_layout?.sha256 === '4119758599d0562cb0dbd9e328273e84ee36526517d3c1d97593bc7dd42ab36b', 'cumulative parent differs');
  require(data.part_count === 1021 && data.counts?.bolt_stacks === 96 && data.counts.spacer_pieces === 16 &&
    data.counts.Hillman_axes === 66 && data.counts.angles === 24, 'inventory differs');
  for (const flag of ['current_response_computed', 'historical_capacity_transferred',
    'complete_conditional_frame_evaluation', 'fabrication_released', 'climbing_released'])
    require(data[flag] === false, 'review boundary differs: '+flag);
  require(data.panel_Hillman_resolution_deferred === true, 'panel deferral differs');
  require(data.stack_updates?.length === 8 && same(data.stack_updates.map(r => r.axis_id).sort(), [...AXES].sort()),
    'eight complete cleat selections required');
  for (const row of data.stack_updates) require(row.selected_product === '8095' && row.selected_spacer_SKU === '13733' &&
    row.selected_underhead_length_mm === 190.5 && row.spacer_piece_count === 1 && row.spacer_piece_length_mm === 25.4 &&
    row.nut_side_spacer_mm === 25.4 && row.minimum_body_mm === 144.272 &&
    row.selected_bolt_grade === 'ASTM A574 alloy steel; partially threaded socket head' &&
    row.selected_nut_SKU === '2584' && row.selected_washer_SKU === '15023' &&
    row.delivered_part_or_thread_window_verified === false && row.Actual === '' && row.Disposition === '', 'hardware recipe differs');
  require(data.removals?.length === 16 && same([...data.removals].sort(),
    AXES.flatMap(id => [id+'_spacer_2', id+'_spacer_3']).sort()), 'only sixteen redundant spacer pieces may be removed');
  require(data.part_transforms?.length === 24 && same(data.part_transforms.map(r => r.name).sort(),
    AXES.flatMap(id => ['shaft', 'spacer', 'nut'].map(role => id+'_'+role)).sort()), 'three changed parts per cleat required');
  for (const row of data.part_transforms) {
    require(AXES.includes(row.axis_id) && row.name === row.axis_id+'_'+row.role && finite(row.translation_xyz_mm), 'part identity differs');
    const scale = {shaft: .9375, spacer: 2, nut: 1}[row.role];
    require(same(row.scale_xyz, [scale, 1, 1]) && row.translation_xyz_mm[1] === 0 && row.translation_xyz_mm[2] === 0,
      'only the checked axial shape change is permitted');
    if (row.role === 'nut') require(Math.abs(Math.abs(row.translation_xyz_mm[0])-12.7) < 1e-9, 'nut shift differs');
  }
  return data;
}

export async function loadSingleSpacerScene(THREE, options) {
  const response = await fetch(options.url);require(response.ok, 'scene request failed');
  const bytes = await response.arrayBuffer();require(await sha256(bytes) === options.expectedSha256, 'scene bytes differ');
  const data = validateSingleSpacers(JSON.parse(new TextDecoder('utf-8', {fatal: true}).decode(bytes)), options.layoutSha256);
  const parent = await loadInwardAngleScene(THREE, {...options, url: data.parent_scene.path.split('/').pop(),
    expectedSha256: data.parent_scene.sha256, decodedSha256: data.parent_scene.decoded_sha256,
    layoutSha256: data.parent_layout.sha256});
  const old = new Map(parent.parts.map(p => [p.name, p])), changed = new Map();
  try {
    for (const row of data.part_transforms) {
      const previous = old.get(row.name);require(previous?.geometry && previous.fabrication.kind === 'bolt', 'parent bolt differs');
      const [x, y, z] = row.scale_xyz, [tx, ty, tz] = row.translation_xyz_mm;
      const matrix = new THREE.Matrix4().set(x, 0, 0, tx, 0, y, 0, ty, 0, 0, z, tz, 0, 0, 0, 1);
      const geometry = previous.geometry.clone().applyMatrix4(matrix);geometry.computeBoundingBox();geometry.computeBoundingSphere();
      const part = {...previous, geometry};delete part.path;changed.set(row.name, part);
    }
    require(data.removals.every(n => old.has(n)), 'removed spacer missing');
    const selections = new Map(data.stack_updates.map(r => [r.axis_id, r]));
    const parts = parent.parts.filter(p => !data.removals.includes(p.name)).map(p => {
      const part = changed.get(p.name) || p, selection = selections.get(part.fabrication.connection_name);
      if (!selection) return part;
      const f = part.fabrication;
      const box = part.geometry.boundingBox, dimensions = ['x', 'y', 'z'].map(a => box.max[a]-box.min[a]);
      return {...part, fabrication: {...f, ...selection, hardware_role: f.hardware_role, kind: 'bolt',
        stack_roles: ROLES, dimensions_mm: dimensions, owner_frame_revision: data.revision,
        description: f.hardware_role === 'spacer' ? 'One factory steel spacer: 25.4 mm long, 19.05 mm OD, 10.31875 mm ID; actual fit unobserved' :
          '3/8-16 × 7½-inch ASTM A574 socket-cap cleat stack with one factory spacer; nominal geometry and catalog windows checked',
        actual_parts_verified: false, complete_joint_qualified: false}};
    });
    require(parts.length === 1021 && new Set(parts.map(p => p.name)).size === 1021, 'composed census differs');
    for (const part of parent.parts) if (changed.has(part.name) || data.removals.includes(part.name)) part.geometry.dispose();
    return {...parent, parts, design: {...parent.design, key: data.key, qualified_for_design: false},
      meta: {...parent.meta, revision: data.revision, source_sha256: options.expectedSha256, decoded_sha256: null,
        layout_sha256: options.layoutSha256, single_factory_cleat_spacers: 8, spacer_pieces: 16,
        current_response_computed: false, analysis_pass_transferred: false, physical_release: false}};
  } catch (error) {
    for (const part of [...parent.parts, ...changed.values()]) part.geometry?.dispose();
    throw error;
  }
}
