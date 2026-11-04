/**
 * Winget Updater — Windows 11 Edition
 * Daiki Fujita Inspired Awwwards Interactive Engine
 * DirectComposition, Lenis Inertia Momentum, Pinned Track, Web Audio API,
 * MeshPhysicalMaterial 3D Refractive Monolith & Interactive Simulator
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

    playCrystalShatter() {
      if (!this.enabled || !this.ctx || this.ctx.state !== "running") return;
      try {
        const freqs = [2800, 3400, 2100, 4200, 1800, 3800];
        freqs.forEach((f, idx) => {
          setTimeout(() => {
            if (!this.ctx || this.ctx.state !== "running") return;
            const osc = this.ctx.createOscillator();
            const gain = this.ctx.createGain();
            const now = this.ctx.currentTime;
            osc.type = "sine";
            osc.frequency.setValueAtTime(f, now);
            osc.frequency.exponentialRampToValueAtTime(f * 0.35, now + 0.09);
            gain.gain.setValueAtTime(0.04, now);
            gain.gain.exponentialRampToValueAtTime(0.0001, now + 0.09);
            osc.connect(gain);
            gain.connect(this.ctx.destination);
            osc.start(now);
            osc.stop(now + 0.09);
          }, idx * 18);
        });
      } catch (e) {}
    }

    playCrystalReassemble() {
      if (!this.enabled || !this.ctx || this.ctx.state !== "running") return;
      try {
        const chord = [523.25, 659.25, 783.99, 1046.50, 1318.51];
        chord.forEach((f, idx) => {
          setTimeout(() => {
            if (!this.ctx || this.ctx.state !== "running") return;
            const osc = this.ctx.createOscillator();
            const gain = this.ctx.createGain();
            const now = this.ctx.currentTime;
            osc.type = "triangle";
            osc.frequency.setValueAtTime(f * 0.85, now);
            osc.frequency.exponentialRampToValueAtTime(f, now + 0.14);
            gain.gain.setValueAtTime(0.035, now);
            gain.gain.exponentialRampToValueAtTime(0.0001, now + 0.3);
            osc.connect(gain);
            gain.connect(this.ctx.destination);
            osc.start(now);
            osc.stop(now + 0.3);
          }, idx * 28);
        });
      } catch (e) {}
    }

    playSuccessChime() {
      if (!this.enabled || !this.ctx || this.ctx.state !== "running") return;
      try {
        const chord = [523.25, 659.25, 783.99, 1046.5]; // C major triad
        chord.forEach((f, i) => {
          setTimeout(() => {
            if (!this.ctx || this.ctx.state !== "running") return;
            const osc = this.ctx.createOscillator();
            const gain = this.ctx.createGain();
            const now = this.ctx.currentTime;
            osc.type = "sine";
            osc.frequency.setValueAtTime(f, now);
            gain.gain.setValueAtTime(0.06, now);
            gain.gain.exponentialRampToValueAtTime(0.0001, now + 0.45);
            osc.connect(gain);
            gain.connect(this.ctx.destination);
            osc.start(now);
            osc.stop(now + 0.45);
          }, i * 50);
        });
      } catch (e) {}
    }

    playEnterChord() {
      if (!this.ctx) this.init();
      if (!this.ctx) return;
      try {
        if (this.ctx.state === "suspended") this.ctx.resume().catch(() => {});
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
  // 3. WORLD ATOMIC CLOCKS (Tokyo & Redmond)
  // ==========================================
  const elTyo = document.getElementById("clock-tyo");
  const elRed = document.getElementById("clock-red");

  function updateClocks() {
    const now = new Date();
    try {
      if (elTyo) {
        elTyo.textContent = new Intl.DateTimeFormat("en-US", {
          timeZone: "Asia/Tokyo",
          hour: "2-digit",
          minute: "2-digit",
          second: "2-digit",
          hour12: false,
        }).format(now);
      }
      if (elRed) {
        elRed.textContent = new Intl.DateTimeFormat("en-US", {
          timeZone: "America/Los_Angeles",
          hour: "2-digit",
          minute: "2-digit",
          second: "2-digit",
          hour12: false,
        }).format(now);
      }
    } catch (e) {}
  }
  setInterval(updateClocks, 1000);
  updateClocks();

  // ==========================================
  // 4. TEXT SCRAMBLE / DECRYPT ANIMATION
  // ==========================================
  const scrambleChars = "01X_/*[]—+*^?#アイウエオカキクケコサシスセソ";

  function scrambleText(element, finalText = null, duration = 260) {
    const original = finalText || element.getAttribute("data-original-text") || element.textContent.trim();
    if (!element.getAttribute("data-original-text")) {
      element.setAttribute("data-original-text", original);
    }

    const startTime = performance.now();
    audio.playBlip(1600, 0.02, 0.025);

    function updateFrame(now) {
      const elapsed = now - startTime;
      const progress = Math.min(1, elapsed / duration);
      const revealed = Math.floor(progress * original.length);

      let result = "";
      for (let i = 0; i < original.length; i++) {
        if (original[i] === " " || original[i] === "\n") {
          result += original[i];
        } else if (i < revealed) {
          result += original[i];
        } else {
          result += scrambleChars[Math.floor(Math.random() * scrambleChars.length)];
        }
      }
      element.textContent = result;

      if (progress < 1) {
        requestAnimationFrame(updateFrame);
      } else {
        element.textContent = original;
      }
    }
    requestAnimationFrame(updateFrame);
  }

  document.querySelectorAll("[data-scramble]").forEach((el) => {
    el.setAttribute("data-original-text", el.textContent.trim());
    el.addEventListener("mouseenter", () => {
      scrambleText(el);
    });
  });

  // ==========================================
  // 5. MAGNETIC BUTTON PHYSICS
  // ==========================================
  if (window.matchMedia("(pointer: fine)").matches) {
    document.querySelectorAll("[data-magnetic]").forEach((btn) => {
      btn.addEventListener("mousemove", (e) => {
        const rect = btn.getBoundingClientRect();
        const centerX = rect.left + rect.width / 2;
        const centerY = rect.top + rect.height / 2;
        const deltaX = (e.clientX - centerX) * 0.28;
        const deltaY = (e.clientY - centerY) * 0.28;
        btn.style.transform = `translate3d(${deltaX}px, ${deltaY}px, 0)`;
      });

      btn.addEventListener("mouseleave", () => {
        btn.style.transform = "translate3d(0, 0, 0)";
      });
    });
  }

  // ==========================================
  // 6. 3D CARD PERSPECTIVE TILT
  // ==========================================
  if (window.matchMedia("(pointer: fine)").matches) {
    document.querySelectorAll(".slide-inner, .terminal-shell, .benchmark-table-wrapper").forEach((card) => {
      card.addEventListener("mousemove", (e) => {
        const rect = card.getBoundingClientRect();
        const nx = ((e.clientX - rect.left) / rect.width) * 2 - 1;
        const ny = ((e.clientY - rect.top) / rect.height) * 2 - 1;
        card.style.transform = `perspective(1200px) rotateX(${-ny * 3.5}deg) rotateY(${nx * 3.5}deg)`;
      });

      card.addEventListener("mouseleave", () => {
        card.style.transform = "perspective(1200px) rotateX(0deg) rotateY(0deg)";
      });
    });
  }

  // ==========================================
  // 7. LENIS SMOOTH MOMENTUM SCROLL ENGINE
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
  // 8. [ ENTER ] GATE CONTROLLER
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
  if (window.location.search.includes("preview")) {
    if (enterGate) enterGate.classList.add("dismissed");
    document.documentElement.classList.remove("lenis-stopped");
  }

  window.addEventListener("keydown", (e) => {
    if ((e.key === "Enter" || e.key === " " || e.key === "Escape") && enterGate && !enterGate.classList.contains("dismissed")) {
      unlockExperience();
    }
  });

  // ==========================================
  // 9. PINNED HORIZONTAL WORKS SHOWCASE
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
  // 10. INTERACTIVE LIVE UPDATE SIMULATOR
  // ==========================================
  const hudSimBtn = document.getElementById("hud-sim-btn");
  const hudVerifyBtn = document.getElementById("hud-verify-btn");
  const hudRollbackBtn = document.getElementById("hud-rollback-btn");
  const hudLogs = document.getElementById("hud-logs");
  const neonSpinner = document.getElementById("neon-spinner");
  let simBusy = false;

  function runSimulation(steps, onFinish) {
    if (simBusy || !hudLogs) return;
    simBusy = true;
    hudLogs.innerHTML = "";
    if (neonSpinner) neonSpinner.classList.remove("success");

    let currentStep = 0;
    const interval = setInterval(() => {
      if (currentStep < steps.length) {
        const item = steps[currentStep];
        const logLine = document.createElement("div");
        logLine.className = `hud-log ${item.colorClass}`;
        logLine.textContent = `> ${item.text}`;
        hudLogs.appendChild(logLine);
        audio.playBlip(1100 + currentStep * 150, 0.03, 0.04);
        currentStep++;
      } else {
        clearInterval(interval);
        simBusy = false;
        if (neonSpinner) neonSpinner.classList.add("success");
        audio.playSuccessChime();
        if (onFinish) onFinish();
      }
    }, 450);
  }

  if (hudSimBtn) {
    hudSimBtn.addEventListener("click", () => {
      runSimulation([
        { text: "Querying package manifest: Git.Git v2.48.1...", colorClass: "text-cyan" },
        { text: "Downloading payload [13.3 MB]: 100% complete...", colorClass: "text-cyan" },
        { text: "SHA-256 Authenticode signature: PASS (Trusted)", colorClass: "text-green" },
        { text: "Executing silent unattended DirectComposition installer...", colorClass: "text-amber" },
        { text: "Probing disk binary version: 2.48.1.0 &bull; VERIFIED ACTIVE", colorClass: "text-pink" },
      ]);
    });
  }

  if (hudVerifyBtn) {
    hudVerifyBtn.addEventListener("click", () => {
      runSimulation([
        { text: "Scanning Program Files binaries for Authenticode certificates...", colorClass: "text-cyan" },
        { text: "WinVerifyTrust(WINTRUST_ACTION_GENERIC_VERIFY_V2): SUCCESS", colorClass: "text-green" },
        { text: "Computed SHA256 matches catalog signature exactly.", colorClass: "text-green" },
        { text: "Zero phantom replacement detected: 100% PASS", colorClass: "text-pink" },
      ]);
    });
  }

  if (hudRollbackBtn) {
    hudRollbackBtn.addEventListener("click", () => {
      runSimulation([
        { text: "Initializing Volume Shadow Copy (VSS) delta audit...", colorClass: "text-cyan" },
        { text: "Detected previous stable checkpoint: Build 26300.12...", colorClass: "text-amber" },
        { text: "Restoring registry keys and binary hardlinks...", colorClass: "text-cyan" },
        { text: "Rollback completed cleanly in 142ms &bull; SYSTEM STABLE", colorClass: "text-green" },
      ]);
    });
  }

  // ==========================================
  // 11. SPLIT-LINE REVEALS (IntersectionObserver)
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
  // 12. DISCIPLINES HOVER PREVIEW HUD
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
  // 13. MAGNETIC CUSTOM CURSOR
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
  // 14. THREE.JS DAIKI FUJITA ORGANIC CRYSTAL ROCK WITH COSMIC DREAM PORTAL
  // ==========================================
  const canvas = document.getElementById("hero-webgl-canvas");
  const canvasFrame = document.getElementById("canvas-frame");
  const gemStatusEl = document.getElementById("telemetry-gem-status");
  const gemHintEl = document.getElementById("telemetry-gem-hint");

  let rockGroup, shardMeshes = [], shardData = [], portalGroup, portalLight, ringMesh, causticMesh, pixelBadgeMesh;
  let dirLight1, dirLight2, dirLight3, crystalMat, portalMat, particleSystem;

  if (typeof THREE !== "undefined" && canvas && canvasFrame) {
    try {
      const scene = new THREE.Scene();
      const initialAspect = canvasFrame.clientHeight > 0 ? (canvasFrame.clientWidth / canvasFrame.clientHeight) : 1;
      const camera = new THREE.PerspectiveCamera(42, initialAspect, 0.1, 100);
      camera.position.set(0, 0, 5.2);

      canvas.addEventListener("webglcontextlost", (e) => e.preventDefault(), false);
      const renderer = new THREE.WebGLRenderer({
        canvas: canvas,
        antialias: true,
        alpha: true,
        powerPreference: "high-performance",
      });
      renderer.setSize(canvasFrame.clientWidth, canvasFrame.clientHeight);
      renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));

      // Dynamic Studio HDR PMREM Environment for Real Crystal Refraction
      const pmremGen = new THREE.PMREMGenerator(renderer);
      pmremGen.compileEquirectangularShader();

      const envScene = new THREE.Scene();
      envScene.background = new THREE.Color(0xf1f5f9);

      // Bright specular key card (top-right)
      const cKey = new THREE.Mesh(new THREE.PlaneGeometry(12, 12), new THREE.MeshBasicMaterial({ color: 0xffffff }));
      cKey.position.set(4, 8, 4);
      cKey.lookAt(0, 0, 0);
      envScene.add(cKey);

      // Deep dark contrast card (for crisp internal facet refractions)
      const cDark = new THREE.Mesh(new THREE.PlaneGeometry(10, 10), new THREE.MeshBasicMaterial({ color: 0x09090b }));
      cDark.position.set(-6, -1, -4);
      cDark.lookAt(0, 0, 0);
      envScene.add(cDark);

      // Warm amber caustic card (for Daiki golden caustic sheen)
      const cWarm = new THREE.Mesh(new THREE.PlaneGeometry(8, 8), new THREE.MeshBasicMaterial({ color: 0xfde68a }));
      cWarm.position.set(5, -4, -3);
      cWarm.lookAt(0, 0, 0);
      envScene.add(cWarm);

      const envTarget = pmremGen.fromScene(envScene);
      scene.environment = envTarget.texture;

      rockGroup = new THREE.Group();
      scene.add(rockGroup);

      // --- 1. PROCEDURAL TEXTURES: DREAM PORTAL, ORBITING RING, CAUSTICS, PIXEL BADGE ---
      
      // A. Cosmic Purple Dream Portal Texture
      function createPortalTexture() {
        const size = 512;
        const pCanvas = document.createElement("canvas");
        pCanvas.width = size;
        pCanvas.height = size;
        const ctx = pCanvas.getContext("2d");

        // Cosmic Nebula Radial Glow
        const grad = ctx.createRadialGradient(size / 2, size / 2, 10, size / 2, size / 2, size / 2);
        grad.addColorStop(0.0, "rgba(230, 200, 255, 0.95)");
        grad.addColorStop(0.2, "rgba(147, 51, 234, 0.92)");
        grad.addColorStop(0.55, "rgba(88, 28, 135, 0.88)");
        grad.addColorStop(0.82, "rgba(59, 7, 100, 0.5)");
        grad.addColorStop(1.0, "rgba(30, 3, 50, 0)");
        ctx.fillStyle = grad;
        ctx.beginPath();
        ctx.arc(size / 2, size / 2, size / 2, 0, Math.PI * 2);
        ctx.fill();

        // Concentric Luminous Ripple Rings
        ctx.strokeStyle = "rgba(216, 180, 254, 0.75)";
        ctx.lineWidth = 3;
        ctx.beginPath();
        ctx.arc(size / 2, size / 2, size * 0.35, 0, Math.PI * 2);
        ctx.stroke();

        ctx.strokeStyle = "rgba(192, 132, 252, 0.45)";
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.arc(size / 2, size / 2, size * 0.22, 0, Math.PI * 2);
        ctx.stroke();

        // Center Pulsing Orb
        const centerGrad = ctx.createRadialGradient(size / 2, size / 2, 0, size / 2, size / 2, size * 0.12);
        centerGrad.addColorStop(0, "rgba(255, 255, 255, 1)");
        centerGrad.addColorStop(0.4, "rgba(216, 180, 254, 0.9)");
        centerGrad.addColorStop(1, "rgba(147, 51, 234, 0)");
        ctx.fillStyle = centerGrad;
        ctx.beginPath();
        ctx.arc(size / 2, size / 2, size * 0.12, 0, Math.PI * 2);
        ctx.fill();

        // Typography: ENTER THE DREAM
        ctx.fillStyle = "#ffffff";
        ctx.font = "bold 26px 'Space Grotesk', -apple-system, sans-serif";
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";
        ctx.letterSpacing = "0.15em";
        ctx.shadowColor = "rgba(147, 51, 234, 0.9)";
        ctx.shadowBlur = 12;
        ctx.fillText("ENTER", size / 2, size / 2 - 16);
        ctx.font = "bold 24px 'Space Grotesk', -apple-system, sans-serif";
        ctx.fillText("THE DREAM", size / 2, size / 2 + 18);

        return new THREE.CanvasTexture(pCanvas);
      }

      // B. Orbiting Typography Ring Texture
      function createRingTexture() {
        const rCanvas = document.createElement("canvas");
        rCanvas.width = 1024;
        rCanvas.height = 128;
        const ctx = rCanvas.getContext("2d");
        ctx.clearRect(0, 0, rCanvas.width, rCanvas.height);

        ctx.fillStyle = "rgba(100, 116, 139, 0.85)";
        ctx.font = "bold 22px 'JetBrains Mono', monospace";
        ctx.letterSpacing = "0.22em";
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";

        const text = "WINGET UPDATER // SYSTEM ARCHITECTURE // V1.9.0 // 2026 // TRUTH ENGINE  \u2022  ";
        ctx.fillText(text + text, rCanvas.width / 2, rCanvas.height / 2);

        const tex = new THREE.CanvasTexture(rCanvas);
        tex.wrapS = THREE.RepeatWrapping;
        tex.wrapT = THREE.ClampToEdgeWrapping;
        return tex;
      }

      // C. Caustic Floor Glow Texture
      function createCausticTexture() {
        const cCanvas = document.createElement("canvas");
        cCanvas.width = 512;
        cCanvas.height = 512;
        const ctx = cCanvas.getContext("2d");
        const grad = ctx.createRadialGradient(256, 256, 10, 256, 256, 250);
        grad.addColorStop(0, "rgba(255, 235, 190, 0.45)");
        grad.addColorStop(0.35, "rgba(255, 210, 150, 0.22)");
        grad.addColorStop(0.7, "rgba(255, 190, 120, 0.05)");
        grad.addColorStop(1, "rgba(255, 180, 100, 0)");
        ctx.fillStyle = grad;
        ctx.beginPath();
        ctx.arc(256, 256, 250, 0, Math.PI * 2);
        ctx.fill();
        return new THREE.CanvasTexture(cCanvas);
      }

      // D. Floating Retro Pixel-Art Crystal Badge Texture
      function createPixelBadgeTexture() {
        const bCanvas = document.createElement("canvas");
        bCanvas.width = 64;
        bCanvas.height = 64;
        const ctx = bCanvas.getContext("2d");
        ctx.imageSmoothingEnabled = false;

        // Draw cute 16-bit faceted crystal icon
        const px = (x, y, w, h, col) => {
          ctx.fillStyle = col;
          ctx.fillRect(x * 2, y * 2, w * 2, h * 2);
        };

        // Black outline diamond
        px(10, 2, 12, 2, "#000");
        px(6, 4, 4, 4, "#000");
        px(22, 4, 4, 4, "#000");
        px(3, 8, 3, 6, "#000");
        px(26, 8, 3, 6, "#000");
        px(3, 14, 2, 2, "#000");
        px(27, 14, 2, 2, "#000");
        px(5, 16, 3, 3, "#000");
        px(24, 16, 3, 3, "#000");
        px(8, 19, 4, 4, "#000");
        px(20, 19, 4, 4, "#000");
        px(12, 23, 8, 3, "#000");

        // Ice blue & white gemstone facets
        px(10, 4, 12, 4, "#ffffff");
        px(6, 8, 8, 6, "#cffafe");
        px(14, 8, 8, 6, "#67e8f9");
        px(22, 8, 4, 6, "#06b6d4");
        px(5, 14, 6, 2, "#38bdf8");
        px(11, 14, 10, 5, "#0284c7");
        px(21, 14, 6, 2, "#0369a1");
        px(12, 19, 8, 4, "#0f172a");

        return new THREE.CanvasTexture(bCanvas);
      }

      // --- 2. LIGHTING & ENVIRONMENT ---
      const ambientLight = new THREE.AmbientLight(0xffffff, 1.3);
      scene.add(ambientLight);

      dirLight1 = new THREE.DirectionalLight(0xffffff, 4.5); // Crisp specular key
      dirLight1.position.set(5, 7, 5);
      scene.add(dirLight1);

      dirLight2 = new THREE.DirectionalLight(0xffe082, 3.2); // Warm golden caustic bounce
      dirLight2.position.set(-6, 3, -4);
      scene.add(dirLight2);

      dirLight3 = new THREE.DirectionalLight(0x7dd3fc, 2.8); // Cool cyan chromatic edge
      dirLight3.position.set(3, -5, -4);
      scene.add(dirLight3);

      // --- 3. FLOOR CAUSTIC LIGHT POOL ---
      const causticGeo = new THREE.PlaneGeometry(4.0, 3.0);
      const causticMat = new THREE.MeshBasicMaterial({
        map: createCausticTexture(),
        transparent: true,
        opacity: 0.85,
        depthWrite: false,
      });
      causticMesh = new THREE.Mesh(causticGeo, causticMat);
      causticMesh.position.set(0, -1.6, -0.2);
      causticMesh.rotation.x = -Math.PI / 2.3;
      scene.add(causticMesh);

      // --- 4. ORBITING TYPOGRAPHY RING ---
      const ringGeo = new THREE.CylinderGeometry(2.15, 2.15, 0.22, 64, 1, true);
      const ringMat = new THREE.MeshBasicMaterial({
        map: createRingTexture(),
        transparent: true,
        opacity: 0.7,
        side: THREE.DoubleSide,
        depthWrite: false,
      });
      ringMesh = new THREE.Mesh(ringGeo, ringMat);
      ringMesh.rotation.x = 0.35;
      ringMesh.rotation.z = -0.15;
      scene.add(ringMesh);

      // --- 5. FLOATING PIXEL CRYSTAL BADGE ---
      const badgeGeo = new THREE.PlaneGeometry(0.5, 0.5);
      const badgeMat = new THREE.MeshBasicMaterial({
        map: createPixelBadgeTexture(),
        transparent: true,
        depthWrite: false,
      });
      pixelBadgeMesh = new THREE.Mesh(badgeGeo, badgeMat);
      pixelBadgeMesh.position.set(0.95, 1.25, 0.3);
      scene.add(pixelBadgeMesh);

      // --- 6. COSMIC PURPLE DREAM PORTAL IN CENTER ---
      portalGroup = new THREE.Group();
      portalGroup.position.set(0, 0, -0.35);
      portalGroup.scale.set(0, 0, 0); // hidden until shattered
      rockGroup.add(portalGroup);

      const portalGeo = new THREE.PlaneGeometry(2.8, 2.8);
      portalMat = new THREE.MeshBasicMaterial({
        map: createPortalTexture(),
        transparent: true,
        depthWrite: false,
        side: THREE.DoubleSide,
      });
      const portalDisc = new THREE.Mesh(portalGeo, portalMat);
      portalGroup.add(portalDisc);

      portalLight = new THREE.PointLight(0xa855f7, 0, 8);
      portalLight.position.set(0, 0, 0.1);
      portalGroup.add(portalLight);

      // Floating Ambient Micro-Sparkles
      const pCount = 90;
      const pGeo = new THREE.BufferGeometry();
      const pPos = new Float32Array(pCount * 3);
      for (let i = 0; i < pCount * 3; i += 3) {
        pPos[i] = (Math.random() - 0.5) * 8;
        pPos[i + 1] = (Math.random() - 0.5) * 6;
        pPos[i + 2] = (Math.random() - 0.5) * 6;
      }
      pGeo.setAttribute("position", new THREE.BufferAttribute(pPos, 3));
      const pMat = new THREE.PointsMaterial({
        size: 0.04,
        color: 0x93c5fd,
        transparent: true,
        opacity: 0.7,
      });
      particleSystem = new THREE.Points(pGeo, pMat);
      scene.add(particleSystem);

      // --- 7. LOAD 12 NATURAL SCULPTED CRYSTAL ROCK CHUNKS ---
      const normalMap = new THREE.TextureLoader().load("assets/ice_normal.webp");
      normalMap.wrapS = THREE.RepeatWrapping;
      normalMap.wrapT = THREE.RepeatWrapping;

      // Authentic Translucent Quartz / Ice Crystal Physical Material
      crystalMat = new THREE.MeshPhysicalMaterial({
        color: 0xffffff,
        roughness: 0.14,
        metalness: 0.06,
        transmission: 0.82,
        ior: 1.54, // Quartz
        thickness: 3.2,
        transparent: true,
        opacity: 0.98,
        clearcoat: 1.0,
        clearcoatRoughness: 0.05,
        reflectivity: 0.98,
        envMapIntensity: 2.2,
        normalMap: normalMap,
        normalScale: new THREE.Vector2(1.4, 1.4),
      });

      Promise.all([
        fetch("assets/rock_meta.json").then((r) => r.json()),
        fetch("assets/rock_shards.bin").then((r) => r.arrayBuffer()),
      ]).then(([meta, bin]) => {
        meta.chunks.forEach((c, idx) => {
          const posView = new Float32Array(bin, c.posByteOffset, c.numVerts * 3);
          const normView = new Float32Array(bin, c.normByteOffset, c.numVerts * 3);
          const idxView = new Uint16Array(bin, c.idxByteOffset, c.numIndices);

          const geo = new THREE.BufferGeometry();
          geo.setAttribute("position", new THREE.BufferAttribute(posView, 3));
          geo.setAttribute("normal", new THREE.BufferAttribute(normView, 3));
          geo.setIndex(new THREE.BufferAttribute(idxView, 1));

          const mesh = new THREE.Mesh(geo, crystalMat);
          const centroid = new THREE.Vector3(...c.centroid);
          mesh.position.copy(centroid);
          rockGroup.add(mesh);
          shardMeshes.push(mesh);

          const normC = centroid.clone().normalize();
          const swirl = new THREE.Vector3().crossVectors(normC, new THREE.Vector3(0, 1, 0)).multiplyScalar(0.35);
          const explodeDir = normC.add(swirl).normalize();

          const tumbleAxis = new THREE.Vector3(
            Math.sin(idx * 1.7) * 2 - 1,
            Math.cos(idx * 2.3) * 2 - 1,
            Math.sin(idx * 3.1) * 2 - 1
          ).normalize();

          shardData.push({
            centroid: centroid.clone(),
            explodeDir: explodeDir,
            explodeDist: 2.2 + (Math.sin(idx * 3.7) * 0.5 + 0.5) * 1.8,
            tumbleAxis: tumbleAxis,
            tumbleSpeed: Math.PI * (1.8 + (idx % 4) * 0.7),
            driftSpeed: 0.8 + (idx % 5) * 0.25,
            driftPhase: (idx * 0.45) % (Math.PI * 2),
          });
        });
      }).catch((err) => {
        console.warn("Could not load crystal rock binary:", err);
      });

      // --- 8. PHYSICS, MOUSE SHATTER & REASSEMBLE CONTROLLER ---
      let shatterProgress = 0.0;
      let targetShatter = 0.0;
      let isShatteredState = false;
      let targetLeanX = 0, targetLeanY = 0;
      let isDragging = false;
      let previousPointerX = 0, previousPointerY = 0;
      let dragVelocityX = 0, dragVelocityY = 0;

      if (window.location.search.includes("shatter")) {
        shatterProgress = 1.0;
        targetShatter = 1.0;
        isShatteredState = true;
      }
      function triggerShatter() {
        if (!isShatteredState) {
          isShatteredState = true;
          targetShatter = 1.0;
          if (audio) audio.playCrystalShatter();
          if (gemStatusEl) gemStatusEl.textContent = "COSMIC PURPLE DREAM PORTAL [FRACTURED]";
          if (gemHintEl) gemHintEl.textContent = "CLICK PORTAL OR MOVE AWAY TO REASSEMBLE";
        }
      }

      function triggerReassemble() {
        if (isShatteredState) {
          isShatteredState = false;
          targetShatter = 0.0;
          if (audio) audio.playCrystalReassemble();
          if (gemStatusEl) gemStatusEl.textContent = "QUARTZ CRYSTAL ROCK [SOLID]";
          if (gemHintEl) gemHintEl.textContent = "HOVER TO SHATTER \u2022 LEAVE TO REASSEMBLE";
        }
      }

      canvasFrame.addEventListener("mouseenter", () => {
        triggerShatter();
      });

      canvasFrame.addEventListener("mouseleave", () => {
        triggerReassemble();
        targetLeanX = 0;
        targetLeanY = 0;
      });

      canvasFrame.addEventListener("mousemove", (e) => {
        const rect = canvasFrame.getBoundingClientRect();
        const nx = ((e.clientX - rect.left) / rect.width) * 2 - 1;
        const ny = -(((e.clientY - rect.top) / rect.height) * 2 - 1);
        targetLeanY = nx * 1.2;
        targetLeanX = -ny * 0.8;
      });

      canvasFrame.addEventListener("click", () => {
        if (isShatteredState) {
          // If dream portal is open, clicking it triggers dream mode!
          const dreamBtn = document.getElementById("fixed-theme-btn");
          if (dreamBtn) dreamBtn.click();
          triggerReassemble();
        } else {
          triggerShatter();
        }
      });

      canvasFrame.addEventListener("pointerdown", (e) => {
        isDragging = true;
        previousPointerX = e.clientX;
        previousPointerY = e.clientY;
        dragVelocityX = 0;
        dragVelocityY = 0;
        if (audio) audio.playBlip(1800, 0.02, 0.03);
      });

      window.addEventListener("pointermove", (e) => {
        if (isDragging && rockGroup) {
          const deltaX = e.clientX - previousPointerX;
          const deltaY = e.clientY - previousPointerY;
          dragVelocityX = deltaX * 0.008;
          dragVelocityY = deltaY * 0.008;
          rockGroup.rotation.y += dragVelocityX;
          rockGroup.rotation.x += dragVelocityY;
          previousPointerX = e.clientX;
          previousPointerY = e.clientY;
        }
      });

      window.addEventListener("pointerup", () => {
        isDragging = false;
      });

      // --- 9. THEME PALETTE SWITCHER ---
      window.syncThreePalette = function (isDream) {
        if (!crystalMat) return;
        if (isDream) {
          crystalMat.color.setHex(0xc084fc);
          crystalMat.emissive.setHex(0x2e1065);
          crystalMat.roughness = 0.08;
          crystalMat.transmission = 0.92;
          pMat.color.setHex(0xe879f9);
          dirLight1.color.setHex(0xffffff);
          dirLight2.color.setHex(0xa855f7);
          dirLight3.color.setHex(0x00f0ff);
        } else {
          crystalMat.color.setHex(0xf8fafc);
          crystalMat.emissive.setHex(0x000000);
          crystalMat.roughness = 0.10;
          crystalMat.transmission = 0.94;
          pMat.color.setHex(0x93c5fd);
          dirLight1.color.setHex(0xffffff);
          dirLight2.color.setHex(0xffd166);
          dirLight3.color.setHex(0x38bdf8);
        }
      };

      window.syncThreePalette(document.documentElement.classList.contains("dream-mode"));

      window.addEventListener("resize", () => {
        if (!canvasFrame || !renderer || !camera) return;
        const w = canvasFrame.clientWidth;
        const h = canvasFrame.clientHeight;
        if (w > 0 && h > 0) {
          camera.aspect = w / h;
          camera.updateProjectionMatrix();
          renderer.setSize(w, h);
        }
      });

      const clock = new THREE.Clock();

      function animateThree() {
        requestAnimationFrame(animateThree);
        if (prefersReducedMotion) {
          renderer.render(scene, camera);
          return;
        }

        const elapsed = clock.getElapsedTime();

        // Inertia drag damping & idle rock rotation
        if (!isDragging && rockGroup) {
          dragVelocityX *= 0.92;
          dragVelocityY *= 0.92;
          rockGroup.rotation.y += dragVelocityX + 0.005;
          rockGroup.rotation.x += dragVelocityY + 0.002;
        }

        // Orbiting typography ring rotation
        if (ringMesh) {
          ringMesh.rotation.y = -elapsed * 0.14;
        }

        // Floating pixel badge bobbing
        if (pixelBadgeMesh) {
          pixelBadgeMesh.position.y = 1.25 + Math.sin(elapsed * 2.2) * 0.04;
        }

        // Smooth spring lerp for shatter progress
        shatterProgress += (targetShatter - shatterProgress) * 0.085;
        if (shatterProgress < 0.0008) shatterProgress = 0;

        const easeProgress = 1 - Math.pow(1 - shatterProgress, 3);

        // Update each 3D crystal chunk
        for (let i = 0; i < shardMeshes.length; i++) {
          const mesh = shardMeshes[i];
          const data = shardData[i];
          if (!data) continue;

          if (shatterProgress === 0) {
            mesh.position.copy(data.centroid);
            mesh.quaternion.identity();
            mesh.scale.set(1, 1, 1);
          } else {
            const dist = data.explodeDist * easeProgress;
            const driftX = Math.sin(elapsed * data.driftSpeed + data.driftPhase) * 0.12 * easeProgress;
            const driftY = Math.cos(elapsed * data.driftSpeed * 0.8 + data.driftPhase) * 0.12 * easeProgress;
            const driftZ = Math.sin(elapsed * data.driftSpeed * 1.3 + data.driftPhase) * 0.12 * easeProgress;

            mesh.position.set(
              data.centroid.x + data.explodeDir.x * dist + driftX,
              data.centroid.y + data.explodeDir.y * dist + driftY,
              data.centroid.z + data.explodeDir.z * dist + driftZ
            );

            const angle = data.tumbleSpeed * easeProgress + (elapsed * 0.45 * easeProgress);
            mesh.quaternion.setFromAxisAngle(data.tumbleAxis, angle);

            const s = 1.0 + Math.sin(elapsed * 2.5 + i) * 0.03 * easeProgress;
            mesh.scale.set(s, s, s);
          }
        }

        // Cosmic Purple Dream Portal reveal & spin
        if (portalGroup) {
          const pScale = easeProgress * 1.05;
          portalGroup.scale.set(pScale, pScale, pScale);
          portalGroup.rotation.z = elapsed * 0.22;
        }
        if (portalLight) {
          portalLight.intensity = easeProgress * 4.2;
        }

        // Particle sparkle orbit
        if (particleSystem) {
          particleSystem.rotation.y = elapsed * 0.02;
        }

        // Camera lean toward mouse
        if (isShatteredState && !isDragging) {
          scene.rotation.y += (targetLeanY - scene.rotation.y) * 0.07;
          scene.rotation.x += (targetLeanX - scene.rotation.x) * 0.07;
        } else if (!isDragging) {
          scene.rotation.y += (0 - scene.rotation.y) * 0.05;
          scene.rotation.x += (0 - scene.rotation.x) * 0.05;
        }

        renderer.render(scene, camera);
      }
      animateThree();
    } catch (err) {
      console.warn("WebGL Crystal Rock could not be initialized:", err);
    }
  }

  function updateMonolithOnScroll() {
    if (!rockGroup || prefersReducedMotion) return;
    const scrollY = window.scrollY || document.documentElement.scrollTop;
    rockGroup.rotation.z = scrollY * 0.0015;
  }

  // ==========================================
  // 15. WAKE / DREAM MODE TOGGLE WITH RADIAL IRIS WIPE
  // ==========================================
  const fixedThemeBtn = document.getElementById("fixed-theme-btn");
  const dreamTriggerBtn = document.getElementById("dream-trigger-btn");
  const themeModeText = document.getElementById("theme-mode-text");
  const irisWipe = document.getElementById("iris-wipe");

  function isDreamActive() {
    return document.documentElement.classList.contains("dream-mode");
  }

  function setMode(mode, clickOrigin = null) {
    const isDream = mode === "dream";

    if (irisWipe && clickOrigin) {
      irisWipe.style.clipPath = `circle(0% at ${clickOrigin.x}px ${clickOrigin.y}px)`;
      irisWipe.classList.add("active");
      setTimeout(() => {
        irisWipe.classList.remove("active");
      }, 550);
    }

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

  function toggleTheme(e) {
    const origin = e ? { x: e.clientX, y: e.clientY } : null;
    const nextMode = isDreamActive() ? "wake" : "dream";
    setMode(nextMode, origin);
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
  // 16. TERMINAL COPY CONTROLLER
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
        const textToCopy = codeSnippet.textContent.trim();
        if (navigator.clipboard && navigator.clipboard.writeText) {
          await navigator.clipboard.writeText(textToCopy);
        } else {
          const ta = document.createElement("textarea");
          ta.value = textToCopy;
          ta.style.position = "fixed";
          ta.style.opacity = "0";
          document.body.appendChild(ta);
          ta.select();
          document.execCommand("copy");
          document.body.removeChild(ta);
        }
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

  // ==========================================
  // 17. CINEMATIC THEATER VIDEO CONTROLLER
  // ==========================================
  const launchVideo = document.getElementById("launch-video");
  const theaterCard = document.getElementById("theater-card");
  const playBtn = document.getElementById("play-btn");
  const filmDuration = document.getElementById("film-duration");
  const videoSoundToggle = document.getElementById("video-sound-toggle");
  const videoSoundLabel = document.getElementById("video-sound-label");
  const heroFilmBtn = document.getElementById("hero-film-btn");

  if (launchVideo && theaterCard) {
    function toggleVideoPlay() {
      if (launchVideo.paused) {
        launchVideo.play().then(() => {
          theaterCard.classList.add("playing");
          if (playBtn) playBtn.innerHTML = '<span class="play-icon-shape">&#10074;&#10074;</span>';
          audio.playClick(1400, 500, 0.04);
        }).catch(() => {});
      } else {
        launchVideo.pause();
        theaterCard.classList.remove("playing");
        if (playBtn) playBtn.innerHTML = '<span class="play-icon-shape">&#9654;</span>';
        audio.playClick(900, 400, 0.04);
      }
    }

    if (playBtn) {
      playBtn.addEventListener("click", (e) => {
        e.stopPropagation();
        toggleVideoPlay();
      });
    }

    theaterCard.addEventListener("click", (e) => {
      if (e.target.closest(".sound-toggle-video")) return;
      toggleVideoPlay();
    });

    launchVideo.addEventListener("timeupdate", () => {
      if (!filmDuration) return;
      const cur = Math.floor(launchVideo.currentTime);
      const dur = Math.floor(launchVideo.duration || 20);
      const curSec = cur < 10 ? `0${cur}` : cur;
      const durSec = dur < 10 ? `0${dur}` : dur;
      filmDuration.textContent = `00:${curSec} / 00:${durSec}`;
    });

    launchVideo.addEventListener("ended", () => {
      theaterCard.classList.remove("playing");
      if (playBtn) playBtn.innerHTML = '<span class="play-icon-shape">&#9654;</span>';
      launchVideo.currentTime = 0;
      audio.playSuccessChime();
      showToast("✓ LAUNCH FILM COMPLETE &bull; GET V1.9.0");
    });

    if (videoSoundToggle && videoSoundLabel) {
      videoSoundToggle.addEventListener("click", (e) => {
        e.stopPropagation();
        launchVideo.muted = !launchVideo.muted;
        videoSoundLabel.textContent = launchVideo.muted ? "🔇 Audio: Muted" : "🔊 Audio: Unmuted";
        audio.playBlip(1200, 0.03, 0.03);
      });
    }

    // Auto-pause video when scrolling away
    const videoObserver = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting && !launchVideo.paused) {
          launchVideo.pause();
          theaterCard.classList.remove("playing");
          if (playBtn) playBtn.innerHTML = '<span class="play-icon-shape">&#9654;</span>';
        }
      });
    }, { threshold: 0.25 });
    videoObserver.observe(theaterCard);

    // Hero Watch Film CTA: smoothly scroll down and start
    if (heroFilmBtn) {
      heroFilmBtn.addEventListener("click", (e) => {
        e.preventDefault();
        const filmSec = document.getElementById("film");
        if (filmSec) {
          if (lenis) {
            lenis.scrollTo(filmSec, { offset: -30 });
          } else {
            filmSec.scrollIntoView({ behavior: "smooth" });
          }
          setTimeout(() => {
            if (launchVideo.paused) toggleVideoPlay();
          }, 800);
        }
      });
    }
  }

  // Initialize audio event listeners
  bindAudioTriggers();
})();
