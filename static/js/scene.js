/* ═══════════════════════════════════════════════════════════════════════════
   Formula E — Three.js 3D Scene (CLASSY DIGITAL TWIN EDITION)
   Focuses on sleek, abstract data visualization, fiber-optic tracks,
   and cinematic holographic aesthetics.
   ═══════════════════════════════════════════════════════════════════════════ */

import * as THREE from 'three';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js';

export const sceneState = {
  t3Kw: 0,
  t13Kw: 0,
  liftCoastMeters: 0,
  efficiencyScore: 50,
  sensorFault: false,
  ready: false,
  historicalAvg: 50
};

function hasWebGL() {
  try {
    const c = document.createElement("canvas");
    return !!(c.getContext("webgl2") || c.getContext("webgl"));
  } catch { return false; }
}

if (!hasWebGL()) {
  document.documentElement.classList.add("no-webgl");
  sceneState.ready = false;
}

export async function initScene() {
  if (!hasWebGL()) return;

  const canvas = document.getElementById("scene-canvas");
  if (!canvas) return;

  const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const isMobile = window.innerWidth < 768;

  // ── Renderer (Cinematic Settings) ──────────────────────────────────────
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: false, alpha: false });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.setSize(window.innerWidth, window.innerHeight);
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.0;
  renderer.setClearColor(0x020001, 1); // Deepest obsidian

  // ── Scene & Camera ─────────────────────────────────────────────────────
  const scene = new THREE.Scene();
  scene.fog = new THREE.FogExp2(0x020001, 0.04);

  const camera = new THREE.PerspectiveCamera(45, window.innerWidth / window.innerHeight, 0.1, 200);
  camera.position.set(0, 15, 25);
  camera.lookAt(0, 0, 0);

  // ── Post-Processing (Refined Bloom) ────────────────────────────────────
  const composer = new EffectComposer(renderer);
  const renderPass = new RenderPass(scene, camera);
  composer.addPass(renderPass);

  const bloomPass = new UnrealBloomPass(
      new THREE.Vector2(window.innerWidth, window.innerHeight),
      isMobile ? 0.8 : 1.2,  // Subtler, classier strength
      0.8,                   // Wider radius for a soft glow
      0.15                   // Higher threshold, only brightest things bloom
  );
  composer.addPass(bloomPass);

  // ── Lighting ───────────────────────────────────────────────────────────
  const ambientLight = new THREE.AmbientLight(0x0a0204, 2.0); // Very subtle red ambient
  scene.add(ambientLight);

  // ── Environment (Data Grid Floor) ──────────────────────────────────────
  // Extremely subtle grid for scale, fading into darkness
  const gridHelper = new THREE.GridHelper(100, 50, 0xff1e3c, 0x1a0508);
  gridHelper.position.y = -0.1;
  gridHelper.material.opacity = 0.08;
  gridHelper.material.transparent = true;
  scene.add(gridHelper);

  const floorGeo = new THREE.PlaneGeometry(150, 150);
  const floorMat = new THREE.MeshStandardMaterial({
    color: 0x020001,
    roughness: 0.05, // Mirror-like reflection
    metalness: 1.0,
  });
  const floor = new THREE.Mesh(floorGeo, floorMat);
  floor.rotation.x = -Math.PI / 2;
  floor.position.y = -0.11;
  scene.add(floor);

  // ── The Track (Fiber Optic / Blueprint Splines) ────────────────────────
  const trackPoints = [
    new THREE.Vector3(-12, 0, -10),
    new THREE.Vector3(-5, 0, -14),
    new THREE.Vector3(5, 0, -12),
    new THREE.Vector3(12, 0, -6),
    new THREE.Vector3(14, 0, 0),
    new THREE.Vector3(12, 0, 6),
    new THREE.Vector3(5, 0, 12),
    new THREE.Vector3(-5, 0, 14),
    new THREE.Vector3(-12, 0, 8),
    new THREE.Vector3(-14, 0, 1),
    new THREE.Vector3(-12, 0, -6),
  ];

  const trackCurve = new THREE.CatmullRomCurve3(trackPoints, true, "centripetal", 0.5);
  
  // Create multiple thin parallel lines to represent the track
  const trackGroup = new THREE.Group();
  scene.add(trackGroup);
  
  function createTrackSpline(offsetRadius, colorHex, opacity) {
      const geo = new THREE.TubeGeometry(trackCurve, isMobile ? 100 : 300, offsetRadius, 3, true);
      const mat = new THREE.MeshBasicMaterial({
          color: colorHex,
          transparent: true,
          opacity: opacity,
          wireframe: true // Makes it look like digital laser lines
      });
      const mesh = new THREE.Mesh(geo, mat);
      trackGroup.add(mesh);
  }

  createTrackSpline(0.6, 0xff1e3c, 0.1); // Outer faint wireframe
  createTrackSpline(0.2, 0xff1e3c, 0.3); // Inner core

  // ── Cars (Abstract Energy Pulses) ──────────────────────────────────────
  function createEnergyPulse(colorHex, intensity) {
      const pulseGeo = new THREE.SphereGeometry(0.3, 16, 16);
      const pulseMat = new THREE.MeshBasicMaterial({ color: colorHex });
      const pulse = new THREE.Mesh(pulseGeo, pulseMat);
      
      const light = new THREE.PointLight(colorHex, intensity, 12);
      pulse.add(light);
      
      scene.add(pulse);
      return pulse;
  }

  // Player = Brilliant Crimson, Ghost = Dim Gold/White
  const playerPulse = createEnergyPulse(0xff1e3c, 4.0);
  const ghostPulse = createEnergyPulse(0xffffff, 1.0); 

  // ── Holographic Data Nodes (Regen Zones) ───────────────────────────────
  const TURN3_T = 0.15;   
  const TURN13_T = 0.65;  
  const turn3Pos = trackCurve.getPointAt(TURN3_T);
  const turn13Pos = trackCurve.getPointAt(TURN13_T);

  function createHolographicNode(position) {
      const group = new THREE.Group();
      group.position.copy(position);
      group.position.y = 0;

      // Base ring (Target 500kW)
      const baseGeo = new THREE.TorusGeometry(1.2, 0.02, 16, 64);
      const baseMat = new THREE.MeshBasicMaterial({ color: 0xffd700, transparent: true, opacity: 0.4 });
      const baseRing = new THREE.Mesh(baseGeo, baseMat);
      baseRing.rotation.x = Math.PI / 2;
      group.add(baseRing);

      // Data Core (Grows with KW)
      const coreGeo = new THREE.CylinderGeometry(0.8, 0.8, 1, 32, 1, true);
      const coreMat = new THREE.MeshBasicMaterial({ 
          color: 0x8f0a1c, 
          transparent: true, 
          opacity: 0.6,
          side: THREE.DoubleSide,
          blending: THREE.AdditiveBlending
      });
      const core = new THREE.Mesh(coreGeo, coreMat);
      core.position.y = 0.5;
      core.scale.y = 0.01;
      group.add(core);

      // Limit Ring (600kW)
      const limitGeo = new THREE.TorusGeometry(1.3, 0.01, 16, 64);
      const limitMat = new THREE.MeshBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0.2 });
      const limitRing = new THREE.Mesh(limitGeo, limitMat);
      limitRing.rotation.x = Math.PI / 2;
      limitRing.position.y = 5; // Max height
      group.add(limitRing);

      scene.add(group);
      return { group, core, coreMat, baseRing, limitRing };
  }

  const t3Node = createHolographicNode(turn3Pos);
  const t13Node = createHolographicNode(turn13Pos);

  // ── Subtle Atmospheric Dust (Classy Particles) ─────────────────────────
  const particleCount = isMobile ? 200 : 600;
  const particlesGeo = new THREE.BufferGeometry();
  const particlePositions = new Float32Array(particleCount * 3);
  
  for (let i = 0; i < particleCount; i++) {
    particlePositions[i * 3]     = (Math.random() - 0.5) * 60;
    particlePositions[i * 3 + 1] = Math.random() * 15;
    particlePositions[i * 3 + 2] = (Math.random() - 0.5) * 60;
  }
  
  particlesGeo.setAttribute("position", new THREE.BufferAttribute(particlePositions, 3));
  const particlesMat = new THREE.PointsMaterial({
    color: 0xffffff, size: 0.05, transparent: true, opacity: 0.15, blending: THREE.AdditiveBlending
  });
  const particles = new THREE.Points(particlesGeo, particlesMat);
  if (!reducedMotion) scene.add(particles);

  // ── Cinematic Camera Rig ───────────────────────────────────────────────
  let mouseX = 0, mouseY = 0;
  if (!reducedMotion) {
    document.addEventListener("mousemove", (e) => {
      mouseX = (e.clientX / window.innerWidth - 0.5) * 4;
      mouseY = (e.clientY / window.innerHeight - 0.5) * 2;
    }, { passive: true });
  }

  let carT = 0, ghostCarT = 0;
  let shakeTimer = 0;
  let currentT3Height = 0, currentT13Height = 0;

  function onResize() {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
    composer.setSize(window.innerWidth, window.innerHeight);
  }
  window.addEventListener("resize", onResize, { passive: true });

  let isVisible = true;
  document.addEventListener("visibilitychange", () => { isVisible = !document.hidden; });

  export_triggerFault = () => { shakeTimer = 0.8; };

  const clock = new THREE.Clock();

  function animate() {
    requestAnimationFrame(animate);
    if (!isVisible) return;

    const delta = Math.min(clock.getDelta(), 0.05);
    const elapsed = clock.getElapsedTime();

    // ── Update Holographic Nodes ──
    const targetT3H = Math.min(sceneState.t3Kw, 600) / 600 * 5;
    const targetT13H = Math.min(sceneState.t13Kw, 600) / 600 * 5;
    currentT3Height += (targetT3H - currentT3Height) * 3 * delta;
    currentT13Height += (targetT13H - currentT13Height) * 3 * delta;

    t3Node.core.scale.y = Math.max(0.01, currentT3Height);
    t3Node.core.position.y = currentT3Height / 2;
    t13Node.core.scale.y = Math.max(0.01, currentT13Height);
    t13Node.core.position.y = currentT13Height / 2;

    const updateCoreColor = (node, val) => {
        const isHot = val >= 500;
        node.coreMat.color.setHex(isHot ? 0xff1e3c : 0x4a0510);
        node.coreMat.opacity = isHot ? 0.8 : 0.3;
        node.baseRing.rotation.z = elapsed * 0.5; // Slowly spin target ring
        node.limitRing.rotation.z = -elapsed * 0.3;
    };
    updateCoreColor(t3Node, sceneState.t3Kw);
    updateCoreColor(t13Node, sceneState.t13Kw);

    // ── Update Energy Pulses (Cars) ──
    const scoreNorm = sceneState.efficiencyScore / 100;
    const carSpeed = 0.04 + scoreNorm * 0.08;
    carT = (carT + carSpeed * delta) % 1;
    playerPulse.position.copy(trackCurve.getPointAt(carT));

    const ghostScoreNorm = sceneState.historicalAvg / 100;
    const ghostSpeed = 0.04 + ghostScoreNorm * 0.08;
    ghostCarT = (ghostCarT + ghostSpeed * delta) % 1;
    ghostPulse.position.copy(trackCurve.getPointAt(ghostCarT));

    // ── Rotate Ambient Dust ──
    if (!reducedMotion) {
        particles.rotation.y = elapsed * 0.02;
    }

    // ── Cinematic Camera Movement ──
    // Slowly orbit the center, influenced gently by mouse parallax
    const orbitRadius = 24;
    const orbitSpeed = 0.05;
    const baseCamX = Math.sin(elapsed * orbitSpeed) * orbitRadius;
    const baseCamZ = Math.cos(elapsed * orbitSpeed) * orbitRadius;
    
    const targetCamX = baseCamX + mouseX;
    const targetCamY = 14 - mouseY; // Slight vertical shift
    const targetCamZ = baseCamZ;

    camera.position.x += (targetCamX - camera.position.x) * 2 * delta;
    camera.position.y += (targetCamY - camera.position.y) * 2 * delta;
    camera.position.z += (targetCamZ - camera.position.z) * 2 * delta;
    
    // Always look smoothly at the center
    camera.lookAt(0, 2, 0);

    // ── Sensor Fault Glitch (Subtle but effective) ──
    if (shakeTimer > 0 && !reducedMotion) {
      shakeTimer -= delta;
      bloomPass.strength = 1.2 + Math.random() * 1.5; // Bloom spikes
      camera.position.y += (Math.random() - 0.5) * 0.4;
    } else {
      bloomPass.strength = isMobile ? 0.8 : 1.2;
    }

    composer.render();
  }

  animate();
  sceneState.ready = true;
}

let export_triggerFault = () => {};
export function triggerSensorFault() { export_triggerFault(); }
