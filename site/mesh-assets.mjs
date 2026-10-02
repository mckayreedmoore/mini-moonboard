// Mesh sharing changes storage paths only; frozen part identities and hashes stay intact.
export function validateMeshAliases(data) {
  if (data?.schema !== 'viewer_mesh_aliases/v1' || !data.assets || !data.aliases) {
    throw new Error('Shared mesh alias map is invalid');
  }
  const validPath = path => typeof path === 'string' && path.endsWith('.stl') &&
    !path.startsWith('/') && !path.includes('\\') && !path.split('/').some(p => p === '.' || p === '..' || !p);
  for (const [path, record] of Object.entries(data.assets)) {
    if (!validPath(path) || !/^[0-9a-f]{64}$/.test(record.sha256) || !Number.isInteger(record.bytes) || record.bytes < 0) {
      throw new Error(`Shared mesh record is invalid: ${path}`);
    }
  }
  for (const [path, canonical] of Object.entries(data.aliases)) {
    if (!validPath(path) || Object.hasOwn(data.assets, path) || !Object.hasOwn(data.assets, canonical)) {
      throw new Error(`Shared mesh alias is invalid: ${path}`);
    }
  }
  return data;
}

export async function loadMeshAliases() {
  const response = await fetch(new URL('./mesh-aliases.json', import.meta.url));
  if (!response.ok) throw new Error(`Shared mesh alias map unavailable (HTTP ${response.status})`);
  return validateMeshAliases(await response.json());
}

export function resolveMeshPath(path, data) {
  return Object.hasOwn(data.aliases, path) ? data.aliases[path] : path;
}
