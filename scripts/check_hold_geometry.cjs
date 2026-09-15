// Usage: node scripts/check_hold_geometry.cjs /path/to/three.module.mjs
// Use the same Three.js version as the viewer's import map (currently 0.161.0).
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { pathToFileURL } = require('node:url');

(async () => {
  assert.ok(process.argv[2], 'Provide the local Three.js ES module path.');
  const source = fs.readFileSync(path.join(__dirname, '../site/hold-geometry.js'), 'utf8')
    .replace("from 'three'", `from '${pathToFileURL(path.resolve(process.argv[2])).href}'`);
  const { createHoldMesh } = await import(`data:text/javascript;base64,${Buffer.from(source).toString('base64')}`);
  for (const shape of ['edge', 'pinch', 'sloper', 'jug', 'wedge', 'triangle', 'crescent', 'tapered-pinch', 'fin', 'waisted', 'soft-lobed']) {
    const mesh = createHoldMesh({ shape, width: 100, height: 140, depth: 40, family: 'wood' });
    const geometry = mesh.geometry;
    const { min, max } = geometry.boundingBox;
    for (const [actual, expected] of [[max.x - min.x, 100], [max.y - min.y, 140], [max.z, 40], [min.z, 0]]) {
      assert.ok(Math.abs(actual - expected) < 1e-4, `${shape}: dimensions and mounting plane`);
    }
    assert.ok([...geometry.attributes.position.array, ...geometry.attributes.normal.array].every(Number.isFinite), `${shape}: finite vertices/normals`);
    const points = geometry.attributes.position;
    const indices = geometry.index.array;
    for (let i = 0; i < indices.length; i += 3) {
      const v = [...indices.slice(i, i + 3)].map(index => [points.getX(index), points.getY(index), points.getZ(index)]);
      const a = v[1].map((x, j) => x - v[0][j]);
      const b = v[2].map((x, j) => x - v[0][j]);
      const cross = [a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]];
      assert.ok(Math.hypot(...cross) > 1e-6, `${shape}: nondegenerate triangles`);
    }
    const base = Array.from({ length: 16 }, (_, i) => [points.getX(i), points.getY(i)]);
    if (shape === 'triangle') assert.ok(base[4][1] > -base[12][1], 'Triangle tip faces +Y.');
    if (shape === 'crescent') assert.ok(base[0][1] > base[4][1] && base[8][1] > base[4][1], 'Crescent horns/opening face +Y.');
    if (shape === 'tapered-pinch') assert.ok(Math.abs(base[2][0]) < Math.abs(base[14][0]), 'Pinch narrows toward +Y.');
    if (shape === 'fin') assert.ok(base[2][0] - base[6][0] < base[14][0] - base[10][0], 'Fin narrows toward +Y.');
    if (shape === 'waisted') assert.ok(base[4][1] < base[2][1], 'Waisted hold narrows between rounded ends.');
    if (shape === 'soft-lobed') assert.ok(base[0][0] > -base[8][0] + 5, 'Soft-lobed hold has a leading right lobe.');
    geometry.dispose();
    mesh.material.dispose();
  }
  // These assertions preserve the independently reviewed photo directions in
  // docs/mini-{2020,2025}-viewer-holds.md; they are not installation angles.
  const reviewed = {
    2020: { C12: ['triangle', 180], E11: ['crescent', -10], K7: ['crescent', 45] },
    2025: {
      K12: ['waisted', 0], B11: ['soft-lobed', 0], D11: ['triangle', -10], F11: ['soft-lobed', 20],
      G11: ['triangle', 180], K11: ['crescent', 45], C10: ['fin', 35], I10: ['fin', -40],
      H9: ['tapered-pinch', 0], K7: ['fin', 20], A6: ['waisted', -20], B6: ['crescent', -35],
      H6: ['waisted', 0], K6: ['triangle', 15], F5: ['tapered-pinch', -90], H5: ['fin', -40],
      J4: ['soft-lobed', 25], K3: ['soft-lobed', 20], G2: ['crescent', 0],
    },
  };
  for (const [year, expected] of Object.entries(reviewed)) {
    const { holds } = JSON.parse(fs.readFileSync(path.join(__dirname, `../site/mini-${year}-holds.json`)));
    for (const [position, direction] of Object.entries(expected)) {
      const hold = holds.find(hold => hold.position === position);
      assert.deepEqual([hold.shape, hold.rotation], direction, `${year} ${position}: reviewed orientation`);
    }
  }
  const { holds: holds2025 } = JSON.parse(fs.readFileSync(path.join(__dirname, '../site/mini-2025-holds.json')));
  const reviewedDimensions = {
    K12: [100, 55], B11: [120, 90], K7: [100, 150], A6: [100, 75], H6: [110, 55], K3: [100, 150],
  };
  for (const [position, dimensions] of Object.entries(reviewedDimensions)) {
    const hold = holds2025.find(hold => hold.position === position);
    assert.deepEqual([hold.width, hold.height], dimensions, `2025 ${position}: reviewed front-view size bucket`);
  }
  console.log('Eleven hold profiles: geometry and reviewed directions pass.');
})().catch(error => { console.error(error); process.exitCode = 1; });
