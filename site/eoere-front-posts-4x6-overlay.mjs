// Solid 4×6 outer kicker posts and their eight revised stacks; parent scenes stay frozen.
import {meshGeometry, sha256, decodeTypedArray} from './wood-joints-overlay.mjs';
import {loadSelectedHardwareBaseScene, loadSelectedHardwareGridScene} from './eoere-selected-hardware-overlay.mjs';

const REVISION = 'eoere-4x6-front-posts-v1';
const POSTS = ['base_post_outer_left', 'base_post_outer_right'];
const AXES = ['cleat_post_bolt_left_1', 'cleat_post_bolt_left_2', 'cleat_post_bolt_right_1', 'cleat_post_bolt_right_2',
  'rail_front_bolt_left_1', 'rail_front_bolt_left_2', 'rail_front_bolt_right_1', 'rail_front_bolt_right_2'];
const SHA = /^[0-9a-f]{64}$/;
const PARENT = {url: 'eoere-selected-hardware-scene.json.gz',
  sha256: '41830cf651f8b0a321a89336f654af5d90a4f42a1d705a7411b5e088de3b2811',
  decoded_sha256: '960caea3fc342224eefa9d5acdaf68a4ee56f6a3f85ab756d29712f8cb7e6baa',
  layout_sha256: 'c16ea7dbda86e6471d6dd1edff44f59e0d0a2db1c3fd1af145ffbd6a8a62ec09'};
const require = (ok, message) => {if (!ok) throw new Error('4×6 posts: ' + message);};

export function validateFrontPosts(data, layoutSha256) {
  require(data?.schema === 'eoere_front_posts_4x6_patch/v1' && data.revision === REVISION &&
    data.candidate === 'compact-floor-flush-eoere-bolted-development', 'revision identity differs');
  require(SHA.test(layoutSha256 || '') && data.layout_report?.sha256 === layoutSha256 &&
    data.layout_report.path === 'docs/wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/occupied-front-posts-4x6-v1.json',
    'geometry binding differs');
  require(Object.entries(PARENT).filter(([key]) => key !== 'layout_sha256').every(([key, value]) =>
    data.parent_scene?.[key] === value) && data.parent_layout?.sha256 === PARENT.layout_sha256, 'parent binding differs');
  require(data.mechanics_ready === false && data.analysis_pass_transferred === false &&
    Object.keys(data.release || {}).length >= 6 && Object.values(data.release).every(v => v === false), 'unresolved release required');
  require(data.keys?.base === 'eoere-4x6-front-posts-frame-development' &&
    data.keys.extra === 'eoere-4x6-front-posts-grid-development', 'viewer keys differ');
  require(Object.entries({base: 1033, extra: 1428, timbers: 22, panels: 6, bolts: 100, screws: 66, spacers: 12})
    .every(([key, count]) => data.counts?.[key] === count), 'part census differs');
  const expected = new Set(POSTS);
  for (const axis of AXES) for (const role of ['shaft', 'head', 'head_washer', 'nut_washer', 'nut',
    ...(axis.startsWith('cleat_') ? ['spacer', 'spacer_2'] : [])]) expected.add(axis + '_' + role);
  require(Array.isArray(data.replacements) && data.replacements.length === expected.size &&
    new Set(data.replacements.map(r => r.name)).size === expected.size && data.replacements.every(r =>
      expected.has(r.name) && r.id === r.name && r.mesh && !r.transform && !r.template_id &&
      r.fabrication?.front_post_revision === REVISION &&
      r.fabrication.kind === (POSTS.includes(r.name) ? 'timber' : 'bolt')), 'exact two posts and eight stacks required');
  for (const axis of AXES) {
    const rows = data.replacements.filter(r => r.fabrication.connection_name === axis);
    const roles = ['shaft', 'head', 'head_washer', 'nut_washer', 'nut',
      ...(axis.startsWith('cleat_') ? ['spacer', 'spacer_2'] : [])];
    require(rows.length === roles.length && rows.every(r =>
      roles.includes(r.fabrication.hardware_role) && r.name === axis+'_'+r.fabrication.hardware_role &&
      Array.isArray(r.fabrication.stack_roles) && new Set(r.fabrication.stack_roles).size === roles.length &&
      r.fabrication.stack_roles.every(role => roles.includes(role))), 'selectable complete stack roles required: '+axis);
  }
  return data;
}

async function loadScene(THREE, options, variant) {
  require(SHA.test(options.expectedSha256 || '') && SHA.test(options.decodedSha256 || ''), 'scene hashes required');
  const response = await fetch(options.url);
  require(response.ok, 'scene request failed');
  const encoded = await response.arrayBuffer();
  require(await sha256(encoded) === options.expectedSha256, 'compressed bytes differ');
  const decoded = await new Response(new Blob([encoded]).stream().pipeThrough(new DecompressionStream('gzip'))).arrayBuffer();
  require(await sha256(decoded) === options.decodedSha256, 'decoded bytes differ');
  const data = validateFrontPosts(JSON.parse(new TextDecoder('utf-8', {fatal: true}).decode(decoded)), options.layoutSha256);
  const topologies = new Map();
  for (const [digest, row] of Object.entries(data.triangle_topologies)) {
    require(SHA.test(digest) && ['uint16', 'uint32'].includes(row.triangle_component_type) &&
      Number.isInteger(row.triangle_count) && row.triangle_count > 0 && row.index_count === row.triangle_count * 3,
      'triangle topology differs');
    const indices = decodeTypedArray(row.triangle_indices_base64, row.triangle_component_type, row.index_count);
    require(await sha256(indices.bytes) === digest, 'triangle bytes differ');
    topologies.set(digest, {...row, indices: indices.values});
  }
  const parent = await (variant === 'base' ? loadSelectedHardwareBaseScene : loadSelectedHardwareGridScene)(THREE,
    {...options, url: PARENT.url, expectedSha256: PARENT.sha256,
      decodedSha256: PARENT.decoded_sha256, layoutSha256: PARENT.layout_sha256});
  const allocated = new Set();
  try {
    const old = new Map(parent.parts.map(p => [p.name, p])), changed = new Map(), additions = [];
    for (const row of data.replacements) {
      const geometry = meshGeometry(THREE, row.mesh, topologies); allocated.add(geometry);
      geometry.computeBoundingBox();
      const previous = old.get(row.name) || old.get(row.fabrication.connection_name + '_spacer');
      require(previous?.fabrication.kind === row.fabrication.kind, 'retained part missing: ' + row.name);
      const part = {...previous, name: row.name, geometry, fabrication: {...previous.fabrication, ...row.fabrication,
        dimensions_mm: ['x', 'y', 'z'].map(a => geometry.boundingBox.max[a] - geometry.boundingBox.min[a])}};
      delete part.path;
      if (old.has(row.name)) changed.set(row.name, part);
      else {require(row.name.endsWith('_spacer_2'), 'unknown addition'); additions.push(part);}
    }
    require(changed.size === 46 && additions.length === 4, 'changed-part census differs');
    const parts = [...parent.parts.map(p => changed.get(p.name) || p), ...additions];
    require(parts.length === data.counts[variant] && new Set(parts.map(p => p.name)).size === parts.length,
      'assembled census differs');
    const bounds = parent.bounds_mm.map(p => [...p]);
    for (const part of [...changed.values(), ...additions]) for (const [i, a] of ['x', 'y', 'z'].entries()) {
      bounds[0][i] = Math.min(bounds[0][i], part.geometry.boundingBox.min[a]);
      bounds[1][i] = Math.max(bounds[1][i], part.geometry.boundingBox.max[a]);
    }
    for (const name of changed.keys()) old.get(name).geometry.dispose();
    return {...parent, parts, bounds_mm: bounds,
      design: {...parent.design, key: data.keys[variant], qualified_for_design: false},
      meta: {...parent.meta, revision: REVISION, source_sha256: options.expectedSha256,
        decoded_sha256: options.decodedSha256, layout_sha256: options.layoutSha256,
        unchanged_geometries_reused: parent.parts.length - changed.size, added_spacers: 12,
        new_response_computed: false, analysis_pass_transferred: false, complete_joint_acceptance: false,
        physical_release: false, planning_mass_kg: null}};
  } catch (error) {
    for (const geometry of allocated) geometry.dispose();
    for (const part of parent.parts) part.geometry?.dispose();
    throw error;
  }
}

export const loadFrontPostsBaseScene = (THREE, options) => loadScene(THREE, options, 'base');
export const loadFrontPostsGridScene = (THREE, options) => loadScene(THREE, options, 'extra');
