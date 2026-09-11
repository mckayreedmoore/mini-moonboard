import * as THREE from 'three';

const COLORS = {
  original: 0xf0c72e,
  'school-f': 0x327bc0,
  wood: 0xd0a670,
  'wood-b': 0xc59963,
  'wood-c': 0xdfbb83,
  foot: 0xf0c72e,
};

// Original generic viewer envelopes, not traced individual holds or hardware.
// ponytail: a few polygon rings suggest grip types; replace visuals when licensed assets exist.
const PROFILES = {
  edge: { exponent: 0.55, shoulder: 0.88, crown: 0.62, tilt: 0.18, center: 0.88 },
  pinch: { exponent: 0.8, shoulder: 0.82, crown: 0.45, tilt: 0, center: 1 },
  sloper: { exponent: 1, shoulder: 0.88, crown: 0.5, tilt: 0, center: 1 },
  jug: { exponent: 0.8, shoulder: 0.95, crown: 0.58, tilt: 0.1, center: 0.53 },
  wedge: { exponent: 0.65, shoulder: 0.82, crown: 0.5, tilt: 0.3, center: 0.75 },
};

/** Local XY is the mounting plane at z=0; +Y is up and +Z protrudes, in mm. */
export function createHoldMesh(hold) {
  const { width, height, depth } = hold;
  if (![width, height, depth].every((value) => Number.isFinite(value) && value > 0)) {
    throw new Error('Hold width, height, and depth must be positive millimeters.');
  }
  const profile = PROFILES[hold.shape] ?? PROFILES.edge;
  const segments = 16;
  const vertices = [];
  const indices = [];
  const rings = [
    [1, 0],
    [1, 0.14],
    [profile.shoulder, 0.65],
    [profile.crown, 0.9],
  ];

  for (const [radius, elevation] of rings) {
    for (let i = 0; i < segments; i += 1) {
      const angle = (i / segments) * Math.PI * 2;
      const cosine = Math.cos(angle);
      const sine = Math.sin(angle);
      const x = Math.sign(cosine) * Math.abs(cosine) ** profile.exponent;
      const y = Math.sign(sine) * Math.abs(sine) ** profile.exponent;
      const taper = hold.shape === 'wedge' ? 0.83 - 0.17 * y : 1;
      const z = elevation === 0 ? 0 : elevation + profile.tilt * y * elevation;
      vertices.push((x * radius * taper * width) / 2, (y * radius * height) / 2, z * depth);
    }
  }
  for (let ring = 0; ring < rings.length - 1; ring += 1) {
    for (let i = 0; i < segments; i += 1) {
      const a = ring * segments + i;
      const b = ring * segments + ((i + 1) % segments);
      indices.push(a, b, a + segments, b, b + segments, a + segments);
    }
  }
  const back = vertices.length / 3;
  vertices.push(0, 0, 0);
  const front = vertices.length / 3;
  vertices.push(0, 0, profile.center * depth);
  for (let i = 0; i < segments; i += 1) {
    const next = (i + 1) % segments;
    const last = (rings.length - 1) * segments;
    indices.push(back, next, i, front, last + i, last + next);
  }

  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute('position', new THREE.Float32BufferAttribute(vertices, 3));
  geometry.setIndex(indices);
  geometry.computeBoundingBox();
  const size = geometry.boundingBox.getSize(new THREE.Vector3());
  geometry.scale(width / size.x, height / size.y, depth / size.z);
  geometry.computeVertexNormals();
  geometry.computeBoundingBox();
  const material = new THREE.MeshStandardMaterial({
    color: COLORS[hold.family] ?? COLORS.original,
    roughness: hold.family?.startsWith('wood') ? 0.72 : 0.94,
    metalness: 0,
    flatShading: true,
  });
  const mesh = new THREE.Mesh(geometry, material);
  mesh.castShadow = true;
  mesh.receiveShadow = true;
  return mesh;
}
