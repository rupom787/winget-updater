/**
 * Winget Updater — Windows 11 Edition
 * Daiki Fujita Inspired Awwwards Interactive Engine
 * DirectComposition, Lenis Inertia Momentum, Pinned Track & Web Audio API
 */

(function () {
  "use strict";

  // ==========================================
  // 1. PROCEDURAL WEB AUDIO API SYNTHESIZER
  // ==========================================
  class AudioEngine {
    constructor() {
      this.ctx = null;
      this.enabled = true;
      this.hasInteracted = false;
    }

    init() {
      if (this.ctx) return;
      const AudioCtx = window.AudioContext || window.webkitAudioContext;
      if (AudioCtx) {
        this.ctx = new AudioCtx();
      }
    }

    wake() {
      this.init();
      if (this.ctx && this.ctx.state === "suspended") {
        this.ctx.resume().catch(() => {});
      }
      this.hasInteracted = true;
    }

    toggle() {
      this.wake();
      this.enabled = !this.enabled;
      return this.enabled;
    }

    playBlip(freq = 1400, duration = 0.035, gainLevel = 0.04) {
      if (!this.enabled || !this.ctx || this.ctx.state !== "running") return;
      try {
        const osc = this.ctx.createOscillator();
        const gain = this.ctx.createGain();
        const now = this.ctx.currentTime;

        osc.type = "sine";
        osc.frequency.setValueAtTime(freq, now);
        osc.frequency.exponentialRampToValueAtTime(freq * 0.6, now + duration);

        gain.gain.setValueAtTime(gainLevel, now);
        gain.gain.exponentialRampToValueAtTime(0.0001, now + duration);

        osc.connect(gain);
        gain.connect(this.ctx.destination);

        osc.start(now);
        osc.stop(now + duration);
      } catch (e) {}
    }

    playClick(freqStart = 1600, freqEnd = 400, duration = 0.05, gainLevel = 0.07) {
      if (!this.enabled || !this.ctx || this.ctx.state !== "running") return;
      try {
        const osc = this.ctx.createOscillator();
        const gain = this.ctx.createGain();
        const now = this.ctx.currentTime;

        osc.type = "triangle";
        osc.frequency.setValueAtTime(freqStart, now);
        osc.frequency.exponentialRampToValueAtTime(freqEnd, now + duration);

        gain.gain.setValueAtTime(gainLevel, now);
        gain.gain.exponentialRampToValueAtTime(0.0001, now + duration);

        osc.connect(gain);
        gain.connect(this.ctx.destination);

        osc.start(now);
        osc.stop(now + duration);
      } catch (e) {}
    }

    playChime(isDream = false) {
      if (!this.enabled || !this.ctx || this.ctx.state !== "running") return;
      try {
        const freqs = isDream ? [440, 660, 880, 1320] : [880, 660, 523, 440];
        freqs.forEach((f, idx) => {
          setTimeout(() => {
            if (!this.ctx || this.ctx.state !== "running") return;
            const osc = this.ctx.createOscillator();
            const gain = this.ctx.createGain();
            const now = this.ctx.currentTime;

            osc.type = "sine";
            osc.frequency.setValueAtTime(f, now);

            gain.gain.setValueAtTime(0.05, now);
            gain.gain.exponentialRampToValueAtTime(0.0001, now + 0.35);

            osc.connect(gain);
            gain.connect(this.ctx.destination);

            osc.start(now);
            osc.stop(now + 0.35);
          }, idx * 60);
        });
      } catch (e) {}
    }

    playEnterChord() {
      if (!this.ctx) this.init();
      if (!this.ctx) return;
      try {
        if (this.ctx.state === "suspended") this.ctx.resume();
        const chord = [220, 277.18, 329.63, 440, 659.25];
        chord.forEach((f) => {
          const osc = this.ctx.createOscillator();
          const gain = this.ctx.createGain();
          const now = this.ctx.currentTime;

          osc.type = "sine";
          osc.frequency.setValueAtTime(f, now);
          osc.frequency.linearRampToValueAtTime(f * 1.01, now + 1.2);

          gain.gain.setValueAtTime(0.03, now);
          gain.gain.exponentialRampToValueAtTime(0.0001, now + 1.4);

          osc.connect(gain);
          gain.connect(this.ctx.destination);

          osc.start(now);
          osc.stop(now + 1.5);
        });
      } catch (e) {}
    }
  }

  const audio = new AudioEngine();

  // Attach audio listeners to elements with data-sound
  function bindAudioTriggers() {
    document.querySelectorAll("[data-sound]").forEach((el) => {
      const type = el.getAttribute("data-sound");
      if (type === "hover") {
        el.addEventListener("mouseenter", () => audio.playBlip(1200, 0.03, 0.035));
      } else if (type === "click") {
        el.addEventListener("click", () => audio.playClick(1500, 450, 0.045, 0.06));
      } else if (type === "toggle") {
        el.addEventListener("click", () => {
          const isDream = document.documentElement.classList.contains("dream-mode");
          audio.playChime(isDream);
        });
      }
    });
  }

  // ==========================================
  // 2. SOUND TOGGLE BUTTON
  // ==========================================
  const soundBtn = document.getElementById("sound-btn");
  const soundLabel = document.getElementById("sound-label");

  if (soundBtn) {
    soundBtn.addEventListener("click", () => {
      const isSoundOn = audio.toggle();
      soundBtn.setAttribute("aria-pressed", isSoundOn ? "true" : "false");
      if (soundLabel) soundLabel.textContent = isSoundOn ? "Sound on" : "Sound off";
      showToast(isSoundOn ? "✓ PROCEDURAL AUDIO ENABLED" : "✕ PROCEDURAL AUDIO MUTED");
    });
  }

  // ==========================================
  // 3. LENIS SMOOTH MOMENTUM SCROLL ENGINE
  // ==========================================
  let lenis = null;
  const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  if (typeof Lenis !== "undefined" && !prefersReducedMotion) {
    lenis = new Lenis({
      duration: 1.15,
      easing: (t) => Math.min(1, 1.001 - Math.pow(2, -10 * t)),
      smoothWheel: true,
      touchMultiplier: 1.5,
    });

    function raf(time) {
      lenis.raf(time);
      requestAnimationFrame(raf);
    }
    requestAnimationFrame(raf);
  }

  // ==========================================
  // 4. [ ENTER ] GATE CONTROLLER
  // ==========================================
  const enterGate = document.getElementById("enter-gate");
  const gateBtn = document.getElementById("gate-btn");

  function unlockExperience() {
    audio.wake();
    audio.playEnterChord();
    if (enterGate) {
      enterGate.classList.add("dismissed");
    }
    document.documentElement.classList.remove("lenis-stopped");
    if (soundBtn) {
      soundBtn.setAttribute("aria-pressed", "true");
    }
    if (lenis) {
      lenis.start();
    }
    // Trigger hero split lines
    document.querySelectorAll(".hero-headline .split-line").forEach((l) => l.classList.add("in-view"));
  }

  if (gateBtn) {
    gateBtn.addEventListener("click", unlockExperience);
  }

  window.addEventListener("keydown", (e) => {
    if ((e.key === "Enter" || e.key === " " || e.key === "Escape") && enterGate && !enterGate.classList.contains("dismissed")) {
      unlockExperience();
    }
  });

  // ==========================================
  // 5. PINNED HORIZONTAL WORKS SHOWCASE
  // ==========================================
  const worksSection = document.getElementById("works");
  const worksTrack = document.getElementById("works-track");
  const worksCounter = document.getElementById("works-counter");
  const workSlides = document.querySelectorAll(".work-slide");
  let lastWorkIndex = 0;

  function updatePinnedWorks() {
    if (!worksSection || !worksTrack || prefersReducedMotion) return;

    const rect = worksSection.getBoundingClientRect();
    const sectionHeight = worksSection.offsetHeight;
    const viewHeight = window.innerHeight;
    const totalScrollable = sectionHeight - viewHeight;

    if (totalScrollable <= 0) return;

    const currentScroll = -rect.top;
    const progress = Math.max(0, Math.min(1, currentScroll / totalScrollable));

    // Horizontal track translation across slides
    const numSlides = workSlides.length;
    const maxTranslate = (numSlides - 1) * window.innerWidth;
    const currentTranslateX = progress * maxTranslate;

    worksTrack.style.transform = `translate3d(${-currentTranslateX}px, 0, 0)`;

    // Active slide counter update (01 / 03)
    const activeIndex = Math.min(numSlides - 1, Math.floor(progress * numSlides + 0.2));
    if (activeIndex !== lastWorkIndex) {
      lastWorkIndex = activeIndex;
      if (worksCounter) {
        worksCounter.textContent = `0${activeIndex + 1} / 0${numSlides}`;
      }
      audio.playBlip(1000 + activeIndex * 200, 0.03, 0.03);
    }

    // Parallax inner screenshot drift
    workSlides.forEach((slide, idx) => {
      const img = slide.querySelector(".slide-img");
      if (img) {
        const slideOffset = (progress * (numSlides - 1) - idx) * 140;
        img.style.transform = `scale(1.04) translate3d(${slideOffset}px, 0, 0)`;
      }
    });
  }

  if (lenis) {
    lenis.on("scroll", () => {
      updatePinnedWorks();
      updateMonolithOnScroll();
    });
  } else {
    window.addEventListener("scroll", () => {
      updatePinnedWorks();
      updateMonolithOnScroll();
    });
  }

  // ==========================================
  // 6. SPLIT-LINE REVEALS (IntersectionObserver)
  // ==========================================
  const splitSections = document.querySelectorAll(".about-section, .disciplines-section, .dream-portal-section, .benchmarks-section, .download-section");
  const lineObserver = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.querySelectorAll(".split-line").forEach((l) => l.classList.add("in-view"));
          entry.target.classList.add("in-view");
        }
      });
    },
    { threshold: 0.15 }
  );

  splitSections.forEach((sec) => lineObserver.observe(sec));

  // ==========================================
  // 7. DISCIPLINES HOVER PREVIEW HUD
  // ==========================================
  const discItems = document.querySelectorAll(".discipline-item");
  const discHover = document.getElementById("disc-hover-preview");
  const hoverCode = document.getElementById("hover-badge-code");
  const hoverTitle = document.getElementById("hover-badge-title");
  const hoverTelemetry = document.getElementById("hover-badge-telemetry");

  const discMetadata = {
    "01": { code: "ORCHESTRATOR // REPO", tele: "WINGET + STORE + NPM + PIP" },
    "02": { code: "TRUTH_ENGINE // SHA256", tele: "AUTHENTICODE DISK AUDIT" },
    "03": { code: "DWM_COMPOSITOR // GPU", tele: "120HZ VELOCITY LERP" },
    "04": { code: "SCHEDULER // LEAN", tele: "0.0% IDLE CPU & ZERO LEAK" },
    "05": { code: "SECURITY // SIGNATURE", tele: "STRICT CERTIFICATE MATCH" },
    "06": { code: "RESILIENCE // SNAPSHOT", tele: "ONE-CLICK ROLLBACK ARMED" },
  };

  let previewX = 0, previewY = 0;
  let targetPreviewX = 0, targetPreviewY = 0;

  if (discHover) {
    discItems.forEach((item) => {
      item.addEventListener("mouseenter", (e) => {
        const idx = item.getAttribute("data-index");
        const title = item.querySelector(".disc-title")?.textContent || "";
        const meta = discMetadata[idx] || { code: "CORE", tele: "ONLINE" };

        if (hoverCode) hoverCode.textContent = meta.code;
        if (hoverTitle) hoverTitle.textContent = title;
        if (hoverTelemetry) hoverTelemetry.textContent = meta.tele;

        targetPreviewX = e.clientX + 24;
        targetPreviewY = e.clientY + 24;
        discHover.classList.add("active");
      });

      item.addEventListener("mousemove", (e) => {
        targetPreviewX = e.clientX + 24;
        targetPreviewY = e.clientY + 24;
      });

      item.addEventListener("mouseleave", () => {
        discHover.classList.remove("active");
      });
    });

    function renderPreview() {
      previewX += (targetPreviewX - previewX) * 0.2;
      previewY += (targetPreviewY - previewY) * 0.2;
      discHover.style.transform = `translate3d(${previewX}px, ${previewY}px, 0)`;
      requestAnimationFrame(renderPreview);
    }
    requestAnimationFrame(renderPreview);
  }

  // ==========================================
  // 8. MAGNETIC CUSTOM CURSOR
  // ==========================================
  const cursor = document.getElementById("custom-cursor");
  let mouseX = window.innerWidth / 2;
  let mouseY = window.innerHeight / 2;
  let curX = mouseX, curY = mouseY;
  let isMoving = false;

  if (window.matchMedia("(pointer: fine)").matches && cursor) {
    window.addEventListener("mousemove", (e) => {
      mouseX = e.clientX;
      mouseY = e.clientY;
      isMoving = true;
    });

    const hoverSelectors = "a, button, .discipline-item, .bm-row, .work-slide, #canvas-frame";
    document.querySelectorAll(hoverSelectors).forEach((el) => {
      el.addEventListener("mouseenter", () => cursor.classList.add("hovering"));
      el.addEventListener("mouseleave", () => cursor.classList.remove("hovering"));
    });

    function renderCursor() {
      if (isMoving) {
        curX += (mouseX - curX) * 0.22;
        curY += (mouseY - curY) * 0.22;
        cursor.style.transform = `translate3d(${curX}px, ${curY}px, 0)`;
      }
      requestAnimationFrame(renderCursor);
    }
    requestAnimationFrame(renderCursor);
  }

  // ==========================================
  // 9. THREE.JS 3D WEBGL MONOLITH VISUALIZER
  // ==========================================
  const canvas = document.getElementById("hero-webgl-canvas");
  const canvasFrame = document.getElementById("canvas-frame");
  let monolithMesh, wireMesh, coreMesh, particleSystem, dirLight1, dirLight2;

  if (typeof THREE !== "undefined" && canvas && canvasFrame) {
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(45, canvasFrame.clientWidth / canvasFrame.clientHeight, 0.1, 100);
    camera.position.set(0, 0, 5.0);

    const renderer = new THREE.WebGLRenderer({
      canvas: canvas,
      antialias: true,
      alpha: true,
      powerPreference: "high-performance",
    });
    renderer.setSize(canvasFrame.clientWidth, canvasFrame.clientHeight);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));

    // Outer Monolith (Octahedron crystal)
    const monolithGeo = new THREE.OctahedronGeometry(1.65, 0);
    const monolithMat = new THREE.MeshStandardMaterial({
      color: 0x991b1b,
      roughness: 0.18,
      metalness: 0.85,
      flatShading: true,
    });
    monolithMesh = new THREE.Mesh(monolithGeo, monolithMat);
    scene.add(monolithMesh);

    // Wireframe Cage
    const wireGeo = new THREE.WireframeGeometry(monolithGeo);
    const wireMat = new THREE.LineBasicMaterial({
      color: 0x0284c7,
      transparent: true,
      opacity: 0.55,
    });
    wireMesh = new THREE.LineSegments(wireGeo, wireMat);
    scene.add(wireMesh);

    // Inner Glowing Core
    const coreGeo = new THREE.IcosahedronGeometry(0.72, 1);
    const coreMat = new THREE.MeshBasicMaterial({
      color: 0x047857,
      wireframe: true,
      transparent: true,
      opacity: 0.7,
    });
    coreMesh = new THREE.Mesh(coreGeo, coreMat);
    scene.add(coreMesh);

    // Floating Ambient Particles
    const pCount = 140;
    const pGeo = new THREE.BufferGeometry();
    const pPos = new Float32Array(pCount * 3);
    for (let i = 0; i < pCount * 3; i += 3) {
      pPos[i] = (Math.random() - 0.5) * 8;
      pPos[i + 1] = (Math.random() - 0.5) * 6;
      pPos[i + 2] = (Math.random() - 0.5) * 6;
    }
    pGeo.setAttribute("position", new THREE.BufferAttribute(pPos, 3));
    const pMat = new THREE.PointsMaterial({
      size: 0.035,
      color: 0x64748b,
      transparent: true,
      opacity: 0.65,
    });
    particleSystem = new THREE.Points(pGeo, pMat);
    scene.add(particleSystem);

    // Lights
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.95);
    scene.add(ambientLight);

    dirLight1 = new THREE.DirectionalLight(0xff2a6d, 2.5);
    dirLight1.position.set(4, 5, 4);
    scene.add(dirLight1);

    dirLight2 = new THREE.DirectionalLight(0x00f0ff, 2.2);
    dirLight2.position.set(-4, -3, 3);
    scene.add(dirLight2);

    // Mouse Lean tracking
    let targetLeanX = 0, targetLeanY = 0;
    let isHoveringCanvas = false;

    canvasFrame.addEventListener("mousemove", (e) => {
      const rect = canvasFrame.getBoundingClientRect();
      const nx = ((e.clientX - rect.left) / rect.width) * 2 - 1;
      const ny = -(((e.clientY - rect.top) / rect.height) * 2 - 1);
      targetLeanY = nx * 1.3;
      targetLeanX = -ny * 0.9;
      isHoveringCanvas = true;
    });

    canvasFrame.addEventListener("mouseleave", () => {
      isHoveringCanvas = false;
      targetLeanX = 0;
      targetLeanY = 0;
    });

    // Theme Switcher for 3D Scene
    window.syncThreePalette = function (isDream) {
      if (!monolithMesh) return;
      if (isDream) {
        monolithMat.color.setHex(0x0e0f2b);
        monolithMat.roughness = 0.1;
        monolithMat.metalness = 0.95;
        wireMat.color.setHex(0x00f0ff);
        coreMat.color.setHex(0xff2a6d);
        pMat.color.setHex(0x00f0ff);
        dirLight1.color.setHex(0x00f0ff);
        dirLight2.color.setHex(0xff2a6d);
      } else {
        monolithMat.color.setHex(0x991b1b);
        monolithMat.roughness = 0.2;
        monolithMat.metalness = 0.8;
        wireMat.color.setHex(0x0284c7);
        coreMat.color.setHex(0x047857);
        pMat.color.setHex(0x64748b);
        dirLight1.color.setHex(0xffffff);
        dirLight2.color.setHex(0x0284c7);
      }
    };

    window.syncThreePalette(document.documentElement.classList.contains("dream-mode"));

    window.addEventListener("resize", () => {
      const w = canvasFrame.clientWidth;
      const h = canvasFrame.clientHeight;
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h);
    });

    const clock = new THREE.Clock();

    function animateThree() {
      requestAnimationFrame(animateThree);
      if (prefersReducedMotion) {
        renderer.render(scene, camera);
        return;
      }

      const elapsed = clock.getElapsedTime();

      monolithMesh.rotation.y += 0.007;
      monolithMesh.rotation.x += 0.0035;
      wireMesh.rotation.copy(monolithMesh.rotation);

      coreMesh.rotation.y -= 0.014;
      coreMesh.rotation.z += 0.007;

      particleSystem.rotation.y = elapsed * 0.025;

      if (isHoveringCanvas) {
        scene.rotation.y += (targetLeanY - scene.rotation.y) * 0.08;
        scene.rotation.x += (targetLeanX - scene.rotation.x) * 0.08;
      } else {
        scene.rotation.y += (0 - scene.rotation.y) * 0.05;
        scene.rotation.x += (0 - scene.rotation.x) * 0.05;
      }

      renderer.render(scene, camera);
    }
    animateThree();
  }

  function updateMonolithOnScroll() {
    if (!monolithMesh || prefersReducedMotion) return;
    const scrollY = window.scrollY || document.documentElement.scrollTop;
    monolithMesh.rotation.z = scrollY * 0.0015;
  }

  // ==========================================
  // 10. WAKE / DREAM MODE TOGGLE
  // ==========================================
  const fixedThemeBtn = document.getElementById("fixed-theme-btn");
  const dreamTriggerBtn = document.getElementById("dream-trigger-btn");
  const themeModeText = document.getElementById("theme-mode-text");

  function isDreamActive() {
    return document.documentElement.classList.contains("dream-mode");
  }

  function setMode(mode) {
    const isDream = mode === "dream";
    if (isDream) {
      document.documentElement.classList.add("dream-mode");
      document.body.classList.remove("wake-mode");
      document.body.classList.add("dream-mode");
      if (themeModeText) themeModeText.textContent = "WAKE [○] / DREAM [●]";
      try { localStorage.setItem("color-scheme", "dark"); } catch (e) {}
    } else {
      document.documentElement.classList.remove("dream-mode");
      document.body.classList.remove("dream-mode");
      document.body.classList.add("wake-mode");
      if (themeModeText) themeModeText.textContent = "WAKE [●] / DREAM [○]";
      try { localStorage.setItem("color-scheme", "light"); } catch (e) {}
    }

    if (window.syncThreePalette) {
      window.syncThreePalette(isDream);
    }
  }

  function toggleTheme() {
    const nextMode = isDreamActive() ? "wake" : "dream";
    setMode(nextMode);
    showToast(nextMode === "dream" ? "DREAM MODE // OBSIDIAN BLUEPRINT" : "WAKE MODE // EDITORIAL PAPER");
  }

  if (fixedThemeBtn) fixedThemeBtn.addEventListener("click", toggleTheme);
  if (dreamTriggerBtn) dreamTriggerBtn.addEventListener("click", toggleTheme);

  // Sync initial state
  if (isDreamActive()) {
    setMode("dream");
  } else {
    setMode("wake");
  }

  // ==========================================
  // 11. TERMINAL COPY CONTROLLER
  // ==========================================
  const copyBtn = document.getElementById("copy-btn");
  const codeSnippet = document.getElementById("code-snippet");
  const toastPill = document.getElementById("toast-pill");
  let toastTimer = null;

  function showToast(msg) {
    if (!toastPill) return;
    toastPill.textContent = msg;
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
        showToast("✓ Copied install command to clipboard!");
        setTimeout(() => {
          copyBtn.textContent = "Copy";
        }, 2200);
      } catch (err) {
        copyBtn.textContent = "Ctrl+C";
      }
    });
  }

  // Initialize audio event listeners
  bindAudioTriggers();
})();
