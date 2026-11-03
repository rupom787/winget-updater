/**
 * Software & Package Updater — Windows 11 Edition
 * Modern Interactive Presentation Engine
 * Features: Three.js 3D Monolith, Custom Cursor, Wake/Dream Mode, Enter Gate
 */

(function () {
  "use strict";

  // --- 1. Custom Pixel / Crosshair Cursor ---
  const cursor = document.getElementById("custom-cursor");
  let mouseX = window.innerWidth / 2;
  let mouseY = window.innerHeight / 2;
  let cursorX = mouseX;
  let cursorY = mouseY;
  let isPointerMoving = false;

  if (window.matchMedia("(pointer: fine)").matches && cursor) {
    window.addEventListener("mousemove", (e) => {
      mouseX = e.clientX;
      mouseY = e.clientY;
      isPointerMoving = true;
    });

    const interactiveSelectors = "a, button, .discipline-row, .benchmark-item, .showcase-card, #hero-canvas";
    document.querySelectorAll(interactiveSelectors).forEach((el) => {
      el.addEventListener("mouseenter", () => cursor.classList.add("hovering"));
      el.addEventListener("mouseleave", () => cursor.classList.remove("hovering"));
    });

    function renderCursor() {
      if (isPointerMoving) {
        cursorX += (mouseX - cursorX) * 0.25;
        cursorY += (mouseY - cursorY) * 0.25;
        cursor.style.transform = `translate3d(${cursorX}px, ${cursorY}px, 0) translate(-50%, -50%)`;
      }
      requestAnimationFrame(renderCursor);
    }
    requestAnimationFrame(renderCursor);
  }

  // --- 2. Enter Gate Experience ---
  const enterGate = document.getElementById("enter-gate");
  const gateBar = document.getElementById("gate-bar");
  const gateCounter = document.getElementById("gate-counter");
  const gateBtn = document.getElementById("gate-enter-btn");

  let progress = 0;
  const gateInterval = setInterval(() => {
    progress += Math.floor(Math.random() * 8) + 4;
    if (progress >= 100) {
      progress = 100;
      clearInterval(gateInterval);
      if (gateBar) gateBar.style.width = "100%";
      if (gateCounter) gateCounter.textContent = "100%";
      if (gateBtn) {
        gateBtn.style.display = "inline-block";
        gateBtn.focus();
      }
    } else {
      if (gateBar) gateBar.style.width = `${progress}%`;
      if (gateCounter) gateCounter.textContent = `${progress < 10 ? "0" : ""}${progress}%`;
    }
  }, 40);

  function closeGate() {
    if (enterGate) {
      enterGate.classList.add("closed");
      setTimeout(() => {
        enterGate.style.display = "none";
      }, 800);
    }
  }

  if (gateBtn) {
    gateBtn.addEventListener("click", closeGate);
  }
  // Allow quick enter on Enter key or Esc
  window.addEventListener("keydown", (e) => {
    if ((e.key === "Enter" || e.key === "Escape") && enterGate && !enterGate.classList.contains("closed")) {
      closeGate();
    }
  });

  // --- 3. Wake Mode / Dream Mode Controller ---
  const dreamBtn = document.getElementById("dream-mode-btn");
  const toggleText = document.getElementById("toggle-text");
  const metaColorScheme = document.querySelector('meta[name="color-scheme"]');

  function isDreamModeActive() {
    return document.documentElement.classList.contains("dream-mode");
  }

  function setMode(mode) {
    if (mode === "dream") {
      document.documentElement.classList.add("dream-mode");
      document.body.classList.remove("wake-mode");
      document.body.classList.add("dream-mode");
      if (toggleText) toggleText.textContent = "WAKE [○] / DREAM [●]";
      if (metaColorScheme) metaColorScheme.content = "dark";
      try { localStorage.setItem("color-scheme", "dark"); } catch (e) {}
    } else {
      document.documentElement.classList.remove("dream-mode");
      document.body.classList.remove("dream-mode");
      document.body.classList.add("wake-mode");
      if (toggleText) toggleText.textContent = "WAKE [●] / DREAM [○]";
      if (metaColorScheme) metaColorScheme.content = "light";
      try { localStorage.setItem("color-scheme", "light"); } catch (e) {}
    }

    if (window.updateThreeTheme) {
      window.updateThreeTheme(mode === "dream");
    }
  }

  // Initial state check
  if (isDreamModeActive()) {
    setMode("dream");
  } else {
    setMode("wake");
  }

  if (dreamBtn) {
    dreamBtn.addEventListener("click", () => {
      setMode(isDreamModeActive() ? "wake" : "dream");
      showToast(isDreamModeActive() ? "DREAM MODE ACTIVATED // OBSIDIAN BLUEPRINT" : "WAKE MODE ACTIVATED // EDITORIAL PAPER");
    });
  }

  // --- 4. Interactive 3D WebGL Monolith (Three.js) ---
  const canvas = document.getElementById("hero-canvas");
  const canvasWrapper = document.getElementById("hero-3d-wrapper");

  if (typeof THREE !== "undefined" && canvas && canvasWrapper) {
    const scene = new THREE.Scene();

    const camera = new THREE.PerspectiveCamera(45, canvasWrapper.clientWidth / canvasWrapper.clientHeight, 0.1, 100);
    camera.position.set(0, 0, 5.2);

    const renderer = new THREE.WebGLRenderer({
      canvas: canvas,
      antialias: true,
      alpha: true,
      powerPreference: "high-performance",
    });
    renderer.setSize(canvasWrapper.clientWidth, canvasWrapper.clientHeight);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));

    // Outer Monolith (Octahedron crystal)
    const geometry = new THREE.OctahedronGeometry(1.6, 0);
    const material = new THREE.MeshStandardMaterial({
      color: 0x7f1d1d,
      roughness: 0.15,
      metalness: 0.85,
      flatShading: true,
    });
    const monolith = new THREE.Mesh(geometry, material);
    scene.add(monolith);

    // Wireframe Cage overlay
    const wireGeo = new THREE.WireframeGeometry(geometry);
    const wireMat = new THREE.LineBasicMaterial({
      color: 0x0284c7,
      transparent: true,
      opacity: 0.6,
      linewidth: 1,
    });
    const wireframe = new THREE.LineSegments(wireGeo, wireMat);
    scene.add(wireframe);

    // Inner Glowing Core
    const coreGeo = new THREE.IcosahedronGeometry(0.7, 1);
    const coreMat = new THREE.MeshBasicMaterial({
      color: 0x059669,
      wireframe: true,
      transparent: true,
      opacity: 0.7,
    });
    const core = new THREE.Mesh(coreGeo, coreMat);
    scene.add(core);

    // Floating Particles
    const particleCount = 120;
    const particleGeo = new THREE.BufferGeometry();
    const positions = new Float32Array(particleCount * 3);
    for (let i = 0; i < particleCount * 3; i += 3) {
      positions[i] = (Math.random() - 0.5) * 8;
      positions[i + 1] = (Math.random() - 0.5) * 6;
      positions[i + 2] = (Math.random() - 0.5) * 6;
    }
    particleGeo.setAttribute("position", new THREE.BufferAttribute(positions, 3));
    const particleMat = new THREE.PointsMaterial({
      size: 0.04,
      color: 0x64748b,
      transparent: true,
      opacity: 0.7,
    });
    const particles = new THREE.Points(particleGeo, particleMat);
    scene.add(particles);

    // Lights
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.9);
    scene.add(ambientLight);

    const dirLight1 = new THREE.DirectionalLight(0xff2a6d, 2.5);
    dirLight1.position.set(4, 5, 4);
    scene.add(dirLight1);

    const dirLight2 = new THREE.DirectionalLight(0x00f0ff, 2.2);
    dirLight2.position.set(-4, -3, 3);
    scene.add(dirLight2);

    // Mouse Interaction Parallax Lean
    let targetRotX = 0;
    let targetRotY = 0;
    let isMouseOverCanvas = false;

    canvasWrapper.addEventListener("mousemove", (e) => {
      const rect = canvasWrapper.getBoundingClientRect();
      const normX = ((e.clientX - rect.left) / rect.width) * 2 - 1;
      const normY = -(((e.clientY - rect.top) / rect.height) * 2 - 1);
      targetRotY = normX * 1.2;
      targetRotX = -normY * 0.8;
      isMouseOverCanvas = true;
    });

    canvasWrapper.addEventListener("mouseleave", () => {
      isMouseOverCanvas = false;
      targetRotX = 0;
      targetRotY = 0;
    });

    // Theme updater for Three.js
    window.updateThreeTheme = function (isDream) {
      if (isDream) {
        material.color.setHex(0x07080c);
        material.roughness = 0.1;
        material.metalness = 0.95;
        wireMat.color.setHex(0x00f0ff);
        coreMat.color.setHex(0xff2a6d);
        dirLight1.color.setHex(0x00f0ff);
        dirLight2.color.setHex(0xff2a6d);
        particleMat.color.setHex(0x00f0ff);
      } else {
        material.color.setHex(0x7f1d1d);
        material.roughness = 0.2;
        material.metalness = 0.8;
        wireMat.color.setHex(0x0284c7);
        coreMat.color.setHex(0x059669);
        dirLight1.color.setHex(0xffffff);
        dirLight2.color.setHex(0x0284c7);
        particleMat.color.setHex(0x94a3b8);
      }
    };

    window.updateThreeTheme(isDreamModeActive());

    // Responsive Canvas Resize
    window.addEventListener("resize", () => {
      const w = canvasWrapper.clientWidth;
      const h = canvasWrapper.clientHeight;
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h);
    });

    // Render Loop
    const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    let clock = new THREE.Clock();

    function animate() {
      requestAnimationFrame(animate);
      if (prefersReducedMotion) {
        renderer.render(scene, camera);
        return;
      }

      const elapsed = clock.getElapsedTime();

      // Base idle rotation + mouse lean lerp
      monolith.rotation.y += 0.008;
      monolith.rotation.x += 0.004;

      wireframe.rotation.copy(monolith.rotation);

      core.rotation.y -= 0.015;
      core.rotation.z += 0.008;

      particles.rotation.y = elapsed * 0.03;

      if (isMouseOverCanvas) {
        scene.rotation.y += (targetRotY - scene.rotation.y) * 0.08;
        scene.rotation.x += (targetRotX - scene.rotation.x) * 0.08;
      } else {
        scene.rotation.y += (0 - scene.rotation.y) * 0.05;
        scene.rotation.x += (0 - scene.rotation.x) * 0.05;
      }

      renderer.render(scene, camera);
    }
    animate();
  }

  // --- 5. Selected Works / Showcase Paging Controller ---
  const cards = document.querySelectorAll(".showcase-card");
  const counter = document.getElementById("showcase-counter");
  const btnPrev = document.getElementById("showcase-prev");
  const btnNext = document.getElementById("showcase-next");
  let currentIndex = 0;

  function showCard(index) {
    if (cards.length === 0) return;
    if (index < 0) index = cards.length - 1;
    if (index >= cards.length) index = 0;
    currentIndex = index;

    cards.forEach((card, idx) => {
      card.classList.toggle("active", idx === currentIndex);
    });

    if (counter) {
      counter.textContent = `0${currentIndex + 1} / 0${cards.length}`;
    }
  }

  if (btnPrev && btnNext) {
    btnPrev.addEventListener("click", () => showCard(currentIndex - 1));
    btnNext.addEventListener("click", () => showCard(currentIndex + 1));
  }

  // --- 6. Terminal Code Snippet Copy Controller ---
  const copyBtn = document.getElementById("copy-btn");
  const codeSnippet = document.getElementById("code-snippet");
  const toastPill = document.getElementById("toast-pill");
  let toastTimer = null;

  function showToast(message) {
    if (!toastPill) return;
    toastPill.textContent = message;
    toastPill.classList.add("show");
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => {
      toastPill.classList.remove("show");
    }, 2800);
  }

  if (copyBtn && codeSnippet) {
    copyBtn.addEventListener("click", async () => {
      try {
        await navigator.clipboard.writeText(codeSnippet.textContent.trim());
        copyBtn.textContent = "Copied!";
        showToast("✓ Copied terminal install command to clipboard!");
        setTimeout(() => {
          copyBtn.textContent = "Copy";
        }, 2200);
      } catch (err) {
        copyBtn.textContent = "Press Ctrl+C";
      }
    });
  }
})();
