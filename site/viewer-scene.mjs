// Camera, lighting and display transforms. These never modify model coordinates.
import * as THREE from 'three';
import {OrbitControls} from 'https://unpkg.com/three@0.161.0/examples/jsm/controls/OrbitControls.js';

export function createViewerScene() {
  const renderer = new THREE.WebGLRenderer({ antialias: true });
  renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
  document.body.appendChild(renderer.domElement);
  const scene = new THREE.Scene();
  scene.background = new THREE.Color('#121619');
  const camera = new THREE.PerspectiveCamera(42, 1, 1, 10000);
  camera.up.set(0, 0, 1);
  // Initial camera: hold-facing front (the underside climbing face), not
  // the braced support side.
  // Start as an overview: center the board plus front-left scale figure,
  // and leave useful front-to-back space instead of loading close to it.
  camera.position.set(4300, 4700, 1600);
  const controls = new OrbitControls(camera, renderer.domElement);
  controls.target.set(300, 700, 1050);
  if (new URLSearchParams(location.search).get('view') === 'rear') {
    camera.position.set(3700, -4300, 2500);
    controls.target.set(0, -250, 1100);
  }
  controls.enableDamping = true;
  controls.minDistance = 40; // Allow close inspection of individual bolt ends.
  controls.maxDistance = 7000;
  scene.add(new THREE.HemisphereLight(0xffffff, 0x222222, 2.4));
  const key = new THREE.DirectionalLight(0xffffff, 2.5); key.position.set(2000, 2500, 500); scene.add(key);
  const grid = new THREE.GridHelper(5000, 25, 0x6a6256, 0x34302a); grid.rotateX(Math.PI / 2); scene.add(grid);
  // Mirror CAD X for the climber-facing convention: visible left is the A
  // side (where McKay stands); visible right is the K side.
  // Presentation offset only: keep McKay at the established front-left
  // reference point while placing the complete board assembly farther rearward.
  const assemblyView = new THREE.Group(); assemblyView.position.set(0, -950, 0); scene.add(assemblyView);
  const climberView = new THREE.Group(); climberView.scale.x = -1; assemblyView.add(climberView);
  return {renderer, scene, camera, controls, grid, assemblyView, climberView};
}

export function startViewerLoop({renderer, scene, camera, controls}) {
  function resize() { const { innerWidth:w, innerHeight:h } = window; renderer.setSize(w,h); camera.aspect=w/h; camera.zoom=Math.min(1,w/h); camera.updateProjectionMatrix(); }
  addEventListener('resize', resize); resize();
  (function frame() { controls.update(); renderer.render(scene, camera); requestAnimationFrame(frame); })();
}
