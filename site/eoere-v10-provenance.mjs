import {sha256} from './wood-joints-overlay.mjs';

const require = (ok, message) => {if (!ok) throw new Error('V10 provenance: '+message);};
const SHA = /^[a-f0-9]{64}$/;
const PREFIX = 'docs/bolted-frame-development/owner-frame-v10/candidate13/';
export const V10_PROVENANCE_SHA256 = 'de8a8b3581e2bd808d866a10b8e7cf63e0815d21ca2b98d7244eaa2c931418e4';
export const V10_MODEL = 'eoere-owner-frame-v10-development';
export const V10_REVISION = 'eoere-candidate13-side-depth-v10';
export const V10_COUNTS = Object.freeze({Hillman_axes: 66, angles: 24, bolt_stacks: 116,
  occupied_parts: 1167, panels: 6, plywood_cleats: 4, sawn_members: 22, spacer_pieces: 60});
export const V10_SCENE = Object.freeze({url: 'eoere-v10-scene-13.json.gz',
  expectedSha256: '32abbcfcd2552d3df189ea35ab8c1c49d738f447e0dca5d1596eae310766b99f',
  decodedSha256: '9fe54709a8b0d7c0d980b2a783da3377d63175f3c11ee9c3c7b3eeb5a6d08001',
  layoutSha256: 'b79b35e0b159ddea43bb3a1a456f3e34a7acafc2f802c5abb782356e620c0cff'});
const FALSE_FLAGS = ['complete_conditional_frame_evaluation', 'complete_joint_qualified',
  'physical_force_bounds_established', 'physical_operations_authorized', 'structural_acceptance',
  'fabrication_released', 'climbing_released'];
const BINDINGS = {viewer_scene: V10_SCENE.expectedSha256, geometry: V10_SCENE.layoutSha256,
  geometry_raw: '00f54e2f42737455253bab33ac4091b1f94bfd39111f20c52a4b2e0adf8eb6fe',
  clearance: '9a688e1bd46eb5561911b812858f7eedee346c7ee7ed8377155b1bf935cffd40'};

export function isV10RepositoryPath(path) {
  return typeof path === 'string' && path.length > 0 && !path.startsWith('/') &&
    !/[\\:?#]/.test(path) && path.split('/').every(p => p && p !== '.' && p !== '..');
}

export function validateV10Provenance(data) {
  require(data?.schema === 'eoere_v10_candidate13_provenance/v1' &&
    data.model === V10_MODEL && data.geometry_revision === V10_REVISION, 'candidate identity differs');
  for (const flag of FALSE_FLAGS) require(data[flag] === false, 'claim boundary: '+flag);
  for (const [key, value] of Object.entries(V10_COUNTS)) require(data.counts?.[key] === value, 'census differs: '+key);
  require(Object.keys(data.artifacts || {}).length === 29 && Array.isArray(data.support_files) &&
    data.support_files.length === 28, 'frozen root inventory differs');
  const rows = [...Object.values(data.artifacts), ...data.support_files];
  const paths = new Set(), originals = new Set();
  for (const row of rows) {
    require(isV10RepositoryPath(row.source_path) && isV10RepositoryPath(row.integrated?.path) &&
      typeof row.original?.path === 'string' && row.original.path.endsWith('/'+row.source_path), 'invalid relocation path');
    require(row.integrated.path === 'site/'+V10_SCENE.url || row.integrated.path.startsWith(PREFIX), 'target outside candidate namespace');
    require(!paths.has(row.integrated.path) && !originals.has(row.original.path), 'duplicate relocation');
    paths.add(row.integrated.path); originals.add(row.original.path);
    for (const ref of [row.original, row.integrated]) require(SHA.test(ref.sha256 || '') &&
      Number.isInteger(ref.bytes) && ref.bytes > 0, 'invalid file binding');
    const compressed = row.source_path.endsWith('.json') && row.original.bytes > 256000;
    require(row.encoding === (compressed ? 'gzip' : 'identity'), 'encoding policy differs');
    require(row.integrated.path === (row.source_path === 'site/'+V10_SCENE.url ? row.source_path :
      PREFIX+row.source_path+(compressed ? '.gz' : '')), 'relocation target differs');
    if (!compressed) require(row.integrated.sha256 === row.original.sha256 &&
      row.integrated.bytes === row.original.bytes, 'identity bytes differ');
  }
  for (const [name, hash] of Object.entries(BINDINGS)) require(data.artifacts[name]?.original.sha256 === hash, 'frozen binding differs: '+name);
  require(data.scene_decoded_sha256 === V10_SCENE.decodedSha256, 'decoded scene differs');
  require(data.parents?.scene?.path === 'site/eoere-single-spacer-scene.json' &&
    data.parents.scene.sha256 === '250f8fb4e6fc965ebf77dc9a5822ece646a3163fb85878d15c265673275f4058' &&
    data.parents?.layout?.path === 'docs/bolted-frame-development/owner-frame-v9/geometry.json' &&
    data.parents.layout.sha256 === '29db14a7cb6aaf37e5f65ab23f6c9362b1429456a29d4ca02c0e1d5266af00ef', 'parent differs');
  require(Array.isArray(data.paper_audit_artifact_paths) && data.paper_audit_artifact_paths.length === 19 &&
    new Set(data.paper_audit_artifact_paths).size === 19 && data.paper_audit_artifact_paths.every(p => paths.has(p)), 'paper roots differ');
  require(Object.keys(data.center_principal_correction || {}).sort().join(',') === 'index,read_first,record,summary' &&
    Object.values(data.center_principal_correction).every(ref => rows.some(row =>
      row.integrated.path === ref.path && row.integrated.sha256 === ref.sha256 && row.integrated.bytes === ref.bytes)),
    'corrected edge interpretation differs');
  require(rows.some(row => row.integrated.path === data.standards_and_relocation_handoff?.path &&
    row.integrated.sha256 === data.standards_and_relocation_handoff.sha256), 'group and relocation handoff differs');
  require(Array.isArray(data.documents) && data.documents.length > 0 && data.documents.every(row =>
    typeof row.label === 'string' && isV10RepositoryPath(row.path)), 'document routes differ');
  require(data.retained_raw_evidence?.source_package_required_for_replay === true &&
    data.retained_raw_evidence.archive_or_prune_authorized === false, 'raw evidence boundary differs');
  return data;
}

export function resolveV10SourceRef(ref, provenance) {
  const row = [...Object.values(provenance.artifacts), ...provenance.support_files]
    .find(r => r.original.path === ref?.path);
  require(row && row.original.sha256 === ref.sha256, 'unmapped or changed original binding');
  return {...row.integrated, encoding: row.encoding, original: {...row.original}};
}

export function validateV10SceneProvenance(scene, provenance) {
  validateV10Provenance(provenance);
  require(scene.key === provenance.model && scene.revision === provenance.geometry_revision, 'scene identity differs');
  for (const [sceneKey, artifact] of [['layout_report', 'geometry'], ['geometry_source', 'geometry_raw'],
    ['clearance_source', 'clearance']]) {
    const resolved = resolveV10SourceRef(scene[sceneKey], provenance);
    require(resolved.path === provenance.artifacts[artifact].integrated.path, 'scene/source join differs: '+sceneKey);
  }
  for (const [key, value] of Object.entries(V10_COUNTS)) require(scene.counts?.[key] === value, 'scene census differs: '+key);
  require(scene.replacements.length === 150 && scene.additions.length === 146 && scene.removals.length === 0 &&
    scene.part_count === 1167 && scene.parent_part_count === 1021, 'scene patch differs');
  return provenance;
}

export async function loadV10Provenance(url = 'eoere-v10-candidate13-provenance.json') {
  const response = await fetch(url); require(response.ok, 'request failed');
  const bytes = await response.arrayBuffer(); require(await sha256(bytes) === V10_PROVENANCE_SHA256, 'metadata bytes differ');
  return validateV10Provenance(JSON.parse(new TextDecoder('utf-8', {fatal: true}).decode(bytes)));
}
