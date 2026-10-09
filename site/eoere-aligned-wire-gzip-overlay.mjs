// Authenticate and decode the compact asset, then reuse the frozen mesh loader.
import {sha256} from './wood-joints-overlay.mjs';
import {loadEoereAlignedWireScene} from './eoere-aligned-wire-overlay.mjs';

export async function loadEoereAlignedWireGzipScene(THREE, options) {
  if (!/^[0-9a-f]{64}$/.test(options.expectedSha256 || '') ||
      !/^[0-9a-f]{64}$/.test(options.decodedSha256 || '') || typeof DecompressionStream !== 'function')
    throw new Error('Eoere aligned wire: compressed and decoded hashes required');
  const response = await fetch(options.url);
  if (!response.ok) throw new Error(`Eoere aligned wire: compressed request failed (${response.status})`);
  const encoded = await response.arrayBuffer();
  if (await sha256(encoded) !== options.expectedSha256) throw new Error('Eoere aligned wire: compressed bytes differ');
  const decoded = await new Response(new Blob([encoded]).stream().pipeThrough(new DecompressionStream('gzip'))).arrayBuffer();
  if (await sha256(decoded) !== options.decodedSha256) throw new Error('Eoere aligned wire: decoded bytes differ');
  const url = URL.createObjectURL(new Blob([decoded], {type: 'application/json'}));
  try {
    const result = await loadEoereAlignedWireScene(THREE, {...options, url, expectedSha256: options.decodedSha256});
    return {...result, meta: {...result.meta, source_sha256: options.expectedSha256,
      decoded_sha256: options.decodedSha256, compressed_asset_url: options.url}};
  } finally {
    URL.revokeObjectURL(url);
  }
}
