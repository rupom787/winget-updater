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
      setTimeout(() => { enterGate.style.display = "none"; }, 850);
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
    if (enterGate) {
      enterGate.classList.add("dismissed");
      enterGate.style.display = "none";
    }
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

      function updateRockPlacement() {
        if (!rockGroup) return;
        const w = window.innerWidth;
        if (w > 1080) {
          rockGroup.position.set(0.95, -0.05, 0);
          if (causticMesh) causticMesh.position.set(0.95, -1.6, -0.2);
          if (ringMesh) ringMesh.position.set(0.95, -0.05, 0);
        } else if (w > 768) {
          rockGroup.position.set(0.65, -0.1, 0);
          if (causticMesh) causticMesh.position.set(0.65, -1.6, -0.2);
          if (ringMesh) ringMesh.position.set(0.65, -0.1, 0);
        } else {
          rockGroup.position.set(0, -0.55, 0);
          if (causticMesh) causticMesh.position.set(0, -2.1, -0.2);
          if (ringMesh) ringMesh.position.set(0, -0.55, 0);
        }
      }

      // --- BACKGROUND TEXT REFRACTION BUFFER ---
      const backCanvas = document.createElement("canvas");
      backCanvas.width = 1920;
      backCanvas.height = 1080;
      const backCtx = backCanvas.getContext("2d");
      const backTexture = new THREE.CanvasTexture(backCanvas);
      backTexture.minFilter = THREE.LinearFilter;
      backTexture.magFilter = THREE.LinearFilter;

      function updateBackTexture(isDream) {
        const w = window.innerWidth || 1920;
        const h = window.innerHeight || 1080;
        backCanvas.width = Math.min(Math.max(w, 512), 2048);
        backCanvas.height = Math.min(Math.max(h, 512), 2048);
        const bw = backCanvas.width;
        const bh = backCanvas.height;
        backCtx.clearRect(0, 0, bw, bh);

        // Background canvas fill
        backCtx.fillStyle = isDream ? "#07081a" : "#eceae4";
        backCtx.fillRect(0, 0, bw, bh);

        // Architectural vertical grid lines
        backCtx.strokeStyle = isDream ? "rgba(255, 255, 255, 0.04)" : "rgba(0, 0, 0, 0.05)";
        backCtx.lineWidth = 1;
        const numCols = bw > 768 ? 6 : 4;
        for (let i = 1; i < numCols; i++) {
          const gx = (bw / numCols) * i;
          backCtx.beginPath();
          backCtx.moveTo(gx, 0);
          backCtx.lineTo(gx, bh);
          backCtx.stroke();
        }

        // Draw responsive headline text matching page layout
        const padLeft = bw > 768 ? 65 : 24;
        if (bw > 768) {
          backCtx.fillStyle = isDream ? "#a855f7" : "#555555";
          backCtx.font = "500 13px 'DM Mono', monospace";
          backCtx.fillText("WINDOWS 11 BUILD 26300 NATIVE    DIRECTX 12 / DWM COMPOSITION    0.0% IDLE CPU // 13.3 MB", padLeft, 120);

          backCtx.fillStyle = isDream ? "#f8fafc" : "#121212";
          backCtx.font = "600 76px 'Inter Tight', -apple-system, sans-serif";
          backCtx.fillText("Software for updating.", padLeft, 235);

          backCtx.font = "italic 400 92px 'Instrument Serif', Georgia, serif";
          backCtx.fillText("Systems for dreaming.", padLeft, 335);

          backCtx.font = "500 12px 'DM Mono', monospace";
          backCtx.fillStyle = isDream ? "#94a3b8" : "#666666";
          backCtx.fillText("DESKTOP SYSTEM ARCHITECTURE — WINDOWS 11", padLeft, 430);

          backCtx.font = "400 18px 'Inter Tight', sans-serif";
          backCtx.fillText("A high-precision Windows package orchestrator engineered to eliminate", padLeft, 475);
          backCtx.fillText("phantom installer exits, abolish GDI UI micro-stutters, and synthesize", padLeft, 505);
          backCtx.fillText("Winget, Store, Pip, and Npm into one fluid direct-composited reality.", padLeft, 535);
        } else {
          backCtx.fillStyle = isDream ? "#f8fafc" : "#121212";
          backCtx.font = "600 36px 'Inter Tight', -apple-system, sans-serif";
          backCtx.fillText("Software for updating.", padLeft, 160);

          backCtx.font = "italic 400 44px 'Instrument Serif', Georgia, serif";
          backCtx.fillText("Systems for dreaming.", padLeft, 210);
        }

        backTexture.needsUpdate = true;
      }

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

      // D. Floating Retro Pixel-Art Crystal Badge Texture Generator
      function createPixelBadgeTexture(type = "quartz") {
        const bCanvas = document.createElement("canvas");
        bCanvas.width = 64;
        bCanvas.height = 64;
        const ctx = bCanvas.getContext("2d");
        ctx.imageSmoothingEnabled = false;

        const px = (x, y, w, h, col) => {
          ctx.fillStyle = col;
          ctx.fillRect(x * 2, y * 2, w * 2, h * 2);
        };

        if (type === "cloud") {
          // Retro 16-bit cloud badge
          px(11, 4, 10, 2, "#000");
          px(8, 6, 3, 3, "#000");
          px(21, 6, 3, 3, "#000");
          px(4, 9, 4, 3, "#000");
          px(24, 9, 4, 3, "#000");
          px(2, 12, 3, 8, "#000");
          px(28, 12, 3, 8, "#000");
          px(4, 20, 24, 3, "#000");
          px(11, 6, 10, 3, "#ffffff");
          px(8, 9, 16, 4, "#ffffff");
          px(5, 12, 23, 4, "#f0f9ff");
          px(5, 16, 23, 4, "#bae6fd");
          // Golden lightning spark
          px(15, 19, 3, 3, "#facc15");
          px(13, 22, 3, 3, "#facc15");
          px(16, 22, 2, 2, "#eab308");
          px(15, 24, 2, 3, "#facc15");
        } else if (type === "npm") {
          // Retro 16-bit NPM red hexagon badge
          px(10, 3, 12, 2, "#000");
          px(5, 5, 5, 2, "#000");
          px(22, 5, 5, 2, "#000");
          px(3, 7, 2, 16, "#000");
          px(27, 7, 2, 16, "#000");
          px(5, 23, 5, 2, "#000");
          px(22, 23, 5, 2, "#000");
          px(10, 25, 12, 2, "#000");
          px(10, 5, 12, 2, "#ef4444");
          px(5, 7, 22, 16, "#cb3837");
          px(10, 23, 12, 2, "#991b1b");
          // 'npm' lettering
          px(6, 11, 2, 8, "#ffffff"); px(8, 11, 3, 2, "#ffffff"); px(10, 13, 2, 6, "#ffffff");
          px(13, 11, 2, 8, "#ffffff"); px(15, 11, 3, 2, "#ffffff"); px(17, 13, 2, 4, "#ffffff"); px(15, 16, 3, 2, "#ffffff");
          px(20, 11, 2, 8, "#ffffff"); px(22, 11, 2, 2, "#ffffff"); px(23, 13, 2, 6, "#ffffff"); px(24, 11, 2, 2, "#ffffff"); px(25, 11, 2, 8, "#ffffff");
        } else if (type === "php") {
          // Retro 16-bit PHP royal sapphire badge
          px(8, 5, 16, 2, "#000");
          px(4, 7, 4, 3, "#000");
          px(24, 7, 4, 3, "#000");
          px(2, 10, 2, 10, "#000");
          px(28, 10, 2, 10, "#000");
          px(4, 20, 4, 3, "#000");
          px(24, 20, 4, 3, "#000");
          px(8, 23, 16, 2, "#000");
          px(8, 7, 16, 3, "#818cf8");
          px(4, 10, 24, 10, "#4f46e5");
          px(8, 20, 16, 3, "#3730a3");
          // 'php' lettering
          px(6, 12, 2, 7, "#ffffff"); px(8, 12, 2, 2, "#ffffff"); px(9, 13, 2, 3, "#ffffff"); px(8, 15, 2, 2, "#ffffff");
          px(13, 10, 2, 9, "#ffffff"); px(15, 13, 2, 2, "#ffffff"); px(17, 14, 2, 5, "#ffffff");
          px(21, 12, 2, 7, "#ffffff"); px(23, 12, 2, 2, "#ffffff"); px(24, 13, 2, 3, "#ffffff"); px(23, 15, 2, 2, "#ffffff");
        } else if (type === "facebook") {
          // Retro 16-bit Meta / Facebook infinity badge
          px(9, 4, 14, 2, "#000");
          px(5, 6, 4, 3, "#000");
          px(23, 6, 4, 3, "#000");
          px(2, 9, 3, 14, "#000");
          px(27, 9, 3, 14, "#000");
          px(5, 23, 4, 3, "#000");
          px(23, 23, 4, 3, "#000");
          px(9, 26, 14, 2, "#000");
          px(9, 6, 14, 3, "#38bdf8");
          px(5, 9, 22, 7, "#0084ff");
          px(5, 16, 22, 7, "#7c3aed");
          px(9, 23, 14, 3, "#4c1d95");
          // Infinity loop in white / cyan
          px(6, 14, 3, 4, "#ffffff"); px(8, 12, 4, 2, "#ffffff"); px(8, 18, 4, 2, "#ffffff");
          px(12, 13, 3, 2, "#cffafe"); px(14, 15, 4, 2, "#ffffff"); px(17, 17, 3, 2, "#cffafe");
          px(20, 12, 4, 2, "#ffffff"); px(20, 18, 4, 2, "#ffffff"); px(23, 14, 3, 4, "#ffffff");
        } else {
          // Default: 16-bit Daiki Fujita style cyan diamond crystal
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

          px(10, 4, 12, 4, "#ffffff");
          px(6, 8, 8, 6, "#cffafe");
          px(14, 8, 8, 6, "#67e8f9");
          px(22, 8, 4, 6, "#06b6d4");
          px(5, 14, 6, 2, "#38bdf8");
          px(11, 14, 10, 5, "#0284c7");
          px(21, 14, 6, 2, "#0369a1");
          px(12, 19, 8, 4, "#0f172a");
        }

        return new THREE.CanvasTexture(bCanvas);
      }

      const badgeTextures = {
        quartz: createPixelBadgeTexture("quartz"),
        cloud: createPixelBadgeTexture("cloud"),
        npm: createPixelBadgeTexture("npm"),
        php: createPixelBadgeTexture("php"),
        facebook: createPixelBadgeTexture("facebook"),
      };

      // Load high-resolution PNG textures asynchronously
      const texLoader = new THREE.TextureLoader();
      ["quartz", "cloud", "npm", "php", "meta"].forEach((bKey) => {
        const key = bKey === "meta" ? "facebook" : bKey;
        texLoader.load(`assets/badge_${bKey}.png`, (loadedTex) => {
          loadedTex.magFilter = THREE.NearestFilter;
          loadedTex.minFilter = THREE.NearestFilter;
          badgeTextures[key] = loadedTex;
          if (pixelBadgeMesh && typeof CRYSTAL_FORMS !== "undefined" && CRYSTAL_FORMS[currentFormIndex] && CRYSTAL_FORMS[currentFormIndex].badge === key) {
            pixelBadgeMesh.material.map = loadedTex;
            pixelBadgeMesh.material.map.needsUpdate = true;
          }
        });
      });

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

      const dirLightBack = new THREE.DirectionalLight(0xffffff, 2.5); // Rim back light to define 3D shard thickness
      dirLightBack.position.set(-2, 4, -5);
      scene.add(dirLightBack);

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
      const badgeGeo = new THREE.PlaneGeometry(0.50, 0.50);
      const badgeMat = new THREE.MeshBasicMaterial({
        map: badgeTextures.quartz,
        transparent: true,
        depthWrite: false,
      });
      pixelBadgeMesh = new THREE.Mesh(badgeGeo, badgeMat);
      pixelBadgeMesh.position.set(0.12, 1.30, 0.25);
      rockGroup.add(pixelBadgeMesh);

      // --- 5.5 INNER 3D CORE EMBLEMS (Visible inside refractive crystal) ---
      const emblemGroup = new THREE.Group();
      emblemGroup.position.set(0, 0, 0);
      rockGroup.add(emblemGroup);

      const emblemMeshes = {};

      // A. Quartz Crest Emblem (Nested Octahedron)
      const crestGeo = new THREE.OctahedronGeometry(0.38, 0);
      const crestMat = new THREE.MeshPhysicalMaterial({
        color: 0xffffff,
        metalness: 0.85,
        roughness: 0.15,
        transmission: 0.3,
        transparent: true,
        opacity: 0.9,
      });
      emblemMeshes.crest = new THREE.Mesh(crestGeo, crestMat);
      emblemGroup.add(emblemMeshes.crest);

      // B. Cloud Emblem (Stylized 3D puffy cloud lobes)
      const cloudEmblemGroup = new THREE.Group();
      const cloudMat = new THREE.MeshStandardMaterial({
        color: 0x7dd3fc,
        emissive: 0x0284c7,
        emissiveIntensity: 0.65,
        roughness: 0.25,
      });
      const c1 = new THREE.Mesh(new THREE.SphereGeometry(0.20, 16, 16), cloudMat);
      c1.position.set(-0.20, -0.05, 0);
      const c2 = new THREE.Mesh(new THREE.SphereGeometry(0.28, 16, 16), cloudMat);
      c2.position.set(0.04, 0.10, 0);
      const c3 = new THREE.Mesh(new THREE.SphereGeometry(0.22, 16, 16), cloudMat);
      c3.position.set(0.26, -0.02, 0);
      const cBase = new THREE.Mesh(new THREE.CylinderGeometry(0.25, 0.25, 0.12, 16), cloudMat);
      cBase.position.set(0.04, -0.12, 0);
      cBase.rotation.z = Math.PI / 2;
      cloudEmblemGroup.add(c1, c2, c3, cBase);
      cloudEmblemGroup.scale.set(0, 0, 0);
      emblemMeshes.cloud = cloudEmblemGroup;
      emblemGroup.add(cloudEmblemGroup);

      // C. NPM Hexagonal Cube Emblem
      const npmEmblemGroup = new THREE.Group();
      const npmMat = new THREE.MeshStandardMaterial({
        color: 0xef4444,
        emissive: 0x991b1b,
        emissiveIntensity: 0.7,
        metalness: 0.5,
        roughness: 0.2,
      });
      const npmCube = new THREE.Mesh(new THREE.BoxGeometry(0.48, 0.48, 0.48), npmMat);
      npmCube.rotation.set(0.6, 0.78, 0);
      npmEmblemGroup.add(npmCube);
      npmEmblemGroup.scale.set(0, 0, 0);
      emblemMeshes.npm = npmEmblemGroup;
      emblemGroup.add(npmEmblemGroup);

      // D. PHP Oval Sapphire Emblem
      const phpEmblemGroup = new THREE.Group();
      const phpMat = new THREE.MeshStandardMaterial({
        color: 0x6366f1,
        emissive: 0x3730a3,
        emissiveIntensity: 0.65,
        metalness: 0.6,
        roughness: 0.15,
      });
      const phpSphere = new THREE.Mesh(new THREE.SphereGeometry(0.36, 24, 16), phpMat);
      phpSphere.scale.set(1.35, 0.85, 0.65);
      phpEmblemGroup.add(phpSphere);
      phpEmblemGroup.scale.set(0, 0, 0);
      emblemMeshes.php = phpEmblemGroup;
      emblemGroup.add(phpEmblemGroup);

      // E. Meta Infinity Loop Emblem
      const metaEmblemGroup = new THREE.Group();
      const metaMat = new THREE.MeshStandardMaterial({
        color: 0x0084ff,
        emissive: 0x7c3aed,
        emissiveIntensity: 0.75,
        metalness: 0.7,
        roughness: 0.2,
      });
      const metaTorus = new THREE.Mesh(new THREE.TorusKnotGeometry(0.24, 0.065, 64, 16, 2, 3), metaMat);
      metaEmblemGroup.add(metaTorus);
      metaEmblemGroup.scale.set(0, 0, 0);
      emblemMeshes.meta = metaEmblemGroup;
      emblemGroup.add(metaEmblemGroup);

      updateRockPlacement();

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
      const textureLoader = new THREE.TextureLoader();
      const iceNormalMap = textureLoader.load("assets/ice_normal.webp");
      iceNormalMap.wrapS = THREE.RepeatWrapping;
      iceNormalMap.wrapT = THREE.RepeatWrapping;

      const iceMatMap = textureLoader.load("assets/ice_mat.webp");
      iceMatMap.wrapS = THREE.RepeatWrapping;
      iceMatMap.wrapT = THREE.RepeatWrapping;

      const crystalVertexShader = `
        varying vec3 vNormal;
        varying vec3 vViewPosition;
        varying vec3 vWorldPosition;
        varying vec4 vScreenPos;

        void main() {
          vec4 worldPos = modelMatrix * vec4(position, 1.0);
          vWorldPosition = worldPos.xyz;
          vec4 mvPosition = viewMatrix * worldPos;
          vViewPosition = -mvPosition.xyz;
          vNormal = normalize(normalMatrix * normal);
          gl_Position = projectionMatrix * mvPosition;
          vScreenPos = gl_Position;
        }
      `;

      const crystalFragmentShader = `
        precision highp float;

        uniform sampler2D tBack;
        uniform sampler2D tNormal;
        uniform sampler2D tMatcap;
        uniform float uDisp;
        uniform float uRefract;
        uniform float uNight;
        uniform float uTime;

        varying vec3 vNormal;
        varying vec3 vViewPosition;
        varying vec3 vWorldPosition;
        varying vec4 vScreenPos;

        uniform sampler2D tBack;
        uniform sampler2D tNormal;
        uniform sampler2D tMatcap;
        uniform float uDisp;
        uniform float uRefract;
        uniform float uNight;
        uniform float uTime;
        uniform vec3 uFormColor;
        uniform float uFormIntensity;

        void main() {
          vec2 screenUv = (vScreenPos.xy / vScreenPos.w) * 0.5 + 0.5;

          vec3 V = normalize(vViewPosition);
          vec3 N = normalize(vNormal);

          vec2 normUv = vWorldPosition.xy * 0.45 + vWorldPosition.z * 0.12;
          vec3 normalTex = texture2D(tNormal, normUv).rgb * 2.0 - 1.0;
          N = normalize(N + normalTex * 0.38);

          float NdotV = clamp(dot(N, V), 0.0, 1.0);
          float fresnel = pow(1.0 - NdotV, 2.5);

          vec2 refractOffset = vec2(-N.x, N.y) * uRefract;

          float disp = uDisp;
          float r = texture2D(tBack, clamp(screenUv + refractOffset * (1.0 + disp), 0.001, 0.999)).r;
          float g = texture2D(tBack, clamp(screenUv + refractOffset, 0.001, 0.999)).g;
          float b = texture2D(tBack, clamp(screenUv + refractOffset * (1.0 - disp), 0.001, 0.999)).b;
          vec3 refractedColor = vec3(r, g, b);

          vec4 iceVein = texture2D(tMatcap, normUv * 0.75 + vec2(uTime * 0.015, 0.0));

          vec3 light1 = normalize(vec3(0.45, 0.75, 0.55));
          vec3 light2 = normalize(vec3(-0.55, 0.35, 0.4));
          vec3 H1 = normalize(light1 + V);
          vec3 H2 = normalize(light2 + V);
          float spec1 = pow(max(dot(N, H1), 0.0), 55.0) * 1.5;
          float spec2 = pow(max(dot(N, H2), 0.0), 35.0) * 0.75;

          vec3 rainbow = 0.5 + 0.5 * cos(vec3(0.0, 2.0, 4.0) + (NdotV * 5.2 + vWorldPosition.y * 1.8));
          vec3 edgeRainbow = rainbow * fresnel * 0.38;

          vec3 crystalTint;
          if (uNight > 0.5) {
            crystalTint = mix(vec3(0.12, 0.08, 0.28), vec3(0.72, 0.48, 0.98), fresnel);
            refractedColor = mix(refractedColor, vec3(0.85, 0.75, 1.0), 0.3);
          } else {
            crystalTint = mix(vec3(0.88, 0.90, 0.92), vec3(1.0, 1.0, 1.0), fresnel);
          }

          // Dynamic form tint injection (Ruby NPM, Opalescent Cloud, Sapphire PHP, Cyberpunk Meta)
          crystalTint = mix(crystalTint, uFormColor, uFormIntensity);
          refractedColor = mix(refractedColor, uFormColor, uFormIntensity * 0.45);

          vec3 col = mix(refractedColor, crystalTint, 0.24);
          col += iceVein.rgb * 0.06 * (1.0 - uNight * 0.5);
          col += vec3(1.0) * (spec1 + spec2);
          col += edgeRainbow;
          col += vec3(1.0) * fresnel * 0.42;

          float alpha = clamp(0.92 + fresnel * 0.08, 0.0, 1.0);

          gl_FragColor = vec4(col, alpha);
        }
      `;

      crystalMat = new THREE.ShaderMaterial({
        vertexShader: crystalVertexShader,
        fragmentShader: crystalFragmentShader,
        uniforms: {
          tBack: { value: backTexture },
          tNormal: { value: iceNormalMap },
          tMatcap: { value: iceMatMap },
          uDisp: { value: 0.045 },
          uRefract: { value: 0.08 },
          uNight: { value: 0.0 },
          uTime: { value: 0.0 },
          uFormColor: { value: new THREE.Color(1.0, 1.0, 1.0) },
          uFormIntensity: { value: 0.0 },
        },
        transparent: true,
        side: THREE.DoubleSide,
      });

      // --- 7. MULTI-FORM REASSEMBLY ARTIFACT ARCHITECTURE ---
      const CRYSTAL_FORMS = [
        {
          id: "quartz",
          name: "QUARTZ CRYSTAL ROCK [SOLID] • DIRECTX 12",
          hint: "MOVE CURSOR OVER ROCK TO SHATTER",
          color: new THREE.Color(1.0, 1.0, 1.0),
          intensity: 0.0,
          disp: 0.055,
          badge: "quartz",
          emblem: "crest",
          offsets: [
            [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0],
            [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0],
            [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0],
          ],
        },
        {
          id: "cloud",
          name: "CLOUD ARTIFACT [REFORMED] • AWS & AZURE SYNC",
          hint: "MOVE CURSOR OVER CLOUD TO SHATTER",
          color: new THREE.Color(0.55, 0.85, 1.0),
          intensity: 0.65,
          disp: 0.035,
          badge: "cloud",
          emblem: "cloud",
          offsets: [
            [-0.65, 0.15, 0.12], [-0.45, 0.28, -0.08], [-0.22, 0.42, 0.10], [0.12, 0.48, -0.10],
            [0.42, 0.38, 0.08], [0.68, 0.18, -0.05], [0.62, -0.15, 0.12], [0.25, -0.32, -0.10],
            [-0.10, -0.36, 0.14], [-0.42, -0.30, -0.08], [-0.15, 0.08, 0.22], [0.18, 0.05, -0.18],
          ],
        },
        {
          id: "npm",
          name: "NPM REGISTRY RUBY [SOLID] • NODE 22 LTS",
          hint: "MOVE CURSOR OVER NPM RUBY TO SHATTER",
          color: new THREE.Color(0.95, 0.18, 0.18),
          intensity: 0.75,
          disp: 0.048,
          badge: "npm",
          emblem: "npm",
          offsets: [
            [-0.42,  0.42,  0.42], [ 0.42,  0.42,  0.42], [-0.42, -0.42,  0.42], [ 0.42, -0.42,  0.42],
            [-0.42,  0.42, -0.42], [ 0.42,  0.42, -0.42], [-0.42, -0.42, -0.42], [ 0.42, -0.42, -0.42],
            [ 0.00,  0.62,  0.00], [ 0.00, -0.62,  0.00], [-0.62,  0.00,  0.00], [ 0.62,  0.00,  0.00],
          ],
        },
        {
          id: "php",
          name: "PHP RUNTIME SAPPHIRE [SOLID] • OPCACHE 8.4",
          hint: "MOVE CURSOR OVER PHP GEM TO SHATTER",
          color: new THREE.Color(0.38, 0.42, 0.95),
          intensity: 0.72,
          disp: 0.062,
          badge: "php",
          emblem: "php",
          offsets: [
            [-0.82,  0.12,  0.10], [-0.52,  0.38, -0.12], [-0.15,  0.46,  0.12], [ 0.32,  0.40, -0.10],
            [ 0.72,  0.15,  0.10], [ 0.82, -0.22, -0.05], [ 0.38, -0.46,  0.12], [-0.05, -0.48, -0.10],
            [-0.48, -0.44,  0.10], [-0.72, -0.18, -0.10], [-0.22, -0.05,  0.26], [ 0.22,  0.02, -0.22],
          ],
        },
        {
          id: "facebook",
          name: "META DISTRIBUTED FABRIC [SYNCHRONIZED] • REACT & META",
          hint: "MOVE CURSOR OVER META FABRIC TO SHATTER",
          color: new THREE.Color(0.10, 0.52, 1.0),
          intensity: 0.70,
          disp: 0.075,
          badge: "facebook",
          emblem: "meta",
          offsets: [
            [-0.72,  0.32,  0.18], [-0.42,  0.02,  0.00], [-0.72, -0.32, -0.18], [-0.98,  0.00,  0.10],
            [ 0.00,  0.00,  0.00], [ 0.42,  0.00,  0.00], [ 0.72,  0.32, -0.18], [ 0.98,  0.00,  0.10],
            [ 0.72, -0.32,  0.18], [-0.22,  0.22, -0.12], [ 0.22, -0.22,  0.12], [ 0.00,  0.28,  0.05],
          ],
        },
      ];

      let currentFormIndex = 0;
      let reassembleTimer = null;

      // 12 wide scatter trajectories that disperse solid shards across the full screen in 3D
      const scatterConfigs = [
        { dir: new THREE.Vector3(-1.6,  0.8,  0.9).normalize(), dist: 3.3, mass: 1.1, rotSpeed: 2.2 }, // High-left over headline
        { dir: new THREE.Vector3(-1.9, -0.2, -0.7).normalize(), dist: 3.7, mass: 1.4, rotSpeed: 1.8 }, // Mid-left across italic text
        { dir: new THREE.Vector3(-1.4, -1.3,  1.2).normalize(), dist: 3.4, mass: 1.0, rotSpeed: 2.6 }, // Low-left near buttons
        { dir: new THREE.Vector3( 0.2,  1.6, -0.9).normalize(), dist: 2.9, mass: 0.9, rotSpeed: 2.4 }, // High-center towards header
        { dir: new THREE.Vector3( 1.4,  1.3,  0.6).normalize(), dist: 3.3, mass: 1.2, rotSpeed: 2.0 }, // High-right
        { dir: new THREE.Vector3( 1.9,  0.2, -0.5).normalize(), dist: 3.8, mass: 1.5, rotSpeed: 1.6 }, // Far-right edge
        { dir: new THREE.Vector3( 1.5, -1.0,  0.8).normalize(), dist: 3.5, mass: 1.2, rotSpeed: 2.2 }, // Low-right
        { dir: new THREE.Vector3(-0.3, -1.7, -0.6).normalize(), dist: 3.0, mass: 1.3, rotSpeed: 1.9 }, // Low-center towards prompt
        { dir: new THREE.Vector3(-0.9,  1.4, -1.3).normalize(), dist: 3.4, mass: 1.0, rotSpeed: 2.5 }, // Deep-back high-left
        { dir: new THREE.Vector3( 0.9, -1.5,  1.5).normalize(), dist: 3.2, mass: 1.2, rotSpeed: 2.1 }, // Close-front low-right
        { dir: new THREE.Vector3( 1.7, -0.4,  1.0).normalize(), dist: 3.6, mass: 1.4, rotSpeed: 1.7 }, // Close-front right
        { dir: new THREE.Vector3(-1.7,  0.4, -1.0).normalize(), dist: 3.4, mass: 1.1, rotSpeed: 2.3 }, // Deep-back mid-left
      ];

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
          geo.computeVertexNormals(); // Solid chiseled facet normals

          const mesh = new THREE.Mesh(geo, crystalMat);
          const centroid = new THREE.Vector3(...c.centroid);
          mesh.position.copy(centroid);
          rockGroup.add(mesh);
          shardMeshes.push(mesh);

          const cfg = scatterConfigs[idx % scatterConfigs.length];
          const tumbleAxis = new THREE.Vector3(
            Math.sin(idx * 2.3 + 1.1),
            Math.cos(idx * 1.7 + 0.5),
            Math.sin(idx * 3.1 + 2.4)
          ).normalize();

          shardData.push({
            mesh: mesh,
            centroid: centroid.clone(),
            currPos: centroid.clone(),
            formPos: centroid.clone(),
            velocity: new THREE.Vector3(0, 0, 0),
            homeQuat: new THREE.Quaternion(),
            currQuat: new THREE.Quaternion(),
            angVel: new THREE.Vector3(0, 0, 0),
            tumbleAxis: tumbleAxis,
            tumbleSpeed: cfg.rotSpeed,
            scatterDir: cfg.dir,
            scatterDist: cfg.dist,
            mass: cfg.mass,
            driftPhase: (idx * 0.52) % (Math.PI * 2),
            driftSpeed: 0.5 + (idx % 4) * 0.15,
          });
        });

        // Initialize with default quartz form
        applyCurrentForm();

        if (window.location.search.includes("shatter")) {
          isShatteredState = true;
          portalScale = 1.05;
          for (let i = 0; i < shardData.length; i++) {
            const s = shardData[i];
            s.currPos.addScaledVector(s.scatterDir, s.scatterDist * 0.95);
            s.currQuat.setFromAxisAngle(s.tumbleAxis, s.tumbleSpeed * 1.5);
            s.mesh.position.copy(s.currPos);
            s.mesh.quaternion.copy(s.currQuat);
          }
        }
      }).catch((err) => {
        console.warn("Could not load crystal rock binary:", err);
      });

      // --- 8. PHYSICS, MOUSE SHATTER & MULTI-FORM REASSEMBLY CONTROLLER ---
      let isShatteredState = false;
      let portalScale = 0.0;
      let targetLeanX = 0, targetLeanY = 0;
      let isDragging = false;
      let previousPointerX = 0, previousPointerY = 0;
      let dragVelocityX = 0, dragVelocityY = 0;

      function applyCurrentForm() {
        const form = CRYSTAL_FORMS[currentFormIndex];
        if (!form) return;

        // 1. Text Scramble Animation on HUD
        if (gemStatusEl) scrambleText(gemStatusEl, form.name, 350);
        if (gemHintEl) scrambleText(gemHintEl, form.hint, 250);

        // 2. Update floating retro 16-bit pixel badge
        if (pixelBadgeMesh && badgeTextures[form.badge]) {
          pixelBadgeMesh.material.map = badgeTextures[form.badge];
          pixelBadgeMesh.material.map.needsUpdate = true;
        }

        // 3. Update shard form targets (positions & shapes)
        for (let i = 0; i < shardData.length; i++) {
          const s = shardData[i];
          const off = form.offsets[i % form.offsets.length];
          s.formPos = s.centroid.clone().add(new THREE.Vector3(...off));
        }
      }

      if (window.location.search.includes("shatter")) {
        isShatteredState = true;
      }

      function triggerShatter(impulseStrength = 1.0, impactDir = null) {
        if (!isShatteredState) {
          isShatteredState = true;
          if (audio) {
            audio.playCrystalShatter();
            if (audio.playBlip) {
              audio.playBlip(2800, 0.04, 0.08);
              setTimeout(() => audio.playBlip(1600, 0.08, 0.06), 35);
            }
          }

          if (gemStatusEl) gemStatusEl.textContent = "COSMIC PURPLE DREAM PORTAL [FRACTURED]";
          if (gemHintEl) gemHintEl.textContent = "CLICK OR MOVE AWAY TO REASSEMBLE";

          // Natural physics: smooth burst impulse with mass and directional strike
          const str = Math.min(Math.max(impulseStrength, 0.8), 2.2);
          for (let i = 0; i < shardData.length; i++) {
            const s = shardData[i];
            const burstSpeed = (2.6 + (s.scatterDist * 0.75) * str) / s.mass;
            s.velocity.copy(s.scatterDir).multiplyScalar(burstSpeed);
            if (impactDir) {
              s.velocity.addScaledVector(impactDir, 1.4 * str);
            }
            s.angVel.copy(s.tumbleAxis).multiplyScalar(s.tumbleSpeed * 1.8 * str);
          }

          // Auto-reassemble safety timer: automatically reattaches after 2.2 seconds!
          if (reassembleTimer) clearTimeout(reassembleTimer);
          reassembleTimer = setTimeout(() => {
            if (isShatteredState) {
              triggerReassemble();
            }
          }, 2200);
        }
      }

      function triggerReassemble() {
        if (isShatteredState) {
          isShatteredState = false;
          if (reassembleTimer) {
            clearTimeout(reassembleTimer);
            reassembleTimer = null;
          }

          if (audio) {
            audio.playCrystalReassemble();
            if (audio.playBlip) audio.playBlip(1400, 0.04, 0.05);
          }

          // Cycle to the NEXT form on every reassembly!
          currentFormIndex = (currentFormIndex + 1) % CRYSTAL_FORMS.length;
          applyCurrentForm();
        }
      }

      let prevCursorX = 0, prevCursorY = 0, prevCursorTime = performance.now();
      let isInsideRock = false;

      window.addEventListener("mousemove", (e) => {
        const w = window.innerWidth;
        const h = window.innerHeight;
        const now = performance.now();
        const dt = Math.max((now - prevCursorTime) / 1000, 0.001);
        const vx = (e.clientX - prevCursorX) / dt;
        const vy = (e.clientY - prevCursorY) / dt;
        const cursorSpeed = Math.hypot(vx, vy);

        prevCursorX = e.clientX;
        prevCursorY = e.clientY;
        prevCursorTime = now;

        const nx = (e.clientX / w) * 2 - 1;
        const ny = -((e.clientY / h) * 2 - 1);
        targetLeanY = nx * 0.9;
        targetLeanX = -ny * 0.6;

        // Calculate crystal rock screen position precisely in pixels
        if (rockGroup && camera) {
          const rockCenterWorld = rockGroup.position.clone();
          const rockScreen = rockCenterWorld.project(camera);
          const rockPixelX = (rockScreen.x * 0.5 + 0.5) * w;
          const rockPixelY = (-(rockScreen.y * 0.5) + 0.5) * h;

          const distToRock = Math.hypot(e.clientX - rockPixelX, e.clientY - rockPixelY);
          const rockScreenRadius = Math.min(w, h) * (w > 768 ? 0.20 : 0.28);

          // Physical break trigger: cursor strikes or moves into the rock!
          if (distToRock < rockScreenRadius) {
            if (!isInsideRock) {
              isInsideRock = true;
              const impactDir = new THREE.Vector3(vx * 0.002, -vy * 0.002, 0.7).normalize();
              const impact = 1.0 + Math.min(cursorSpeed / 800, 1.4);
              triggerShatter(impact, impactDir);
            }
          } else if (distToRock > rockScreenRadius * 1.15) {
            if (isInsideRock) {
              isInsideRock = false;
            }
            // As soon as cursor leaves the rock radius, start reassembling right away!
            if (isShatteredState) {
              triggerReassemble();
            }
          }
        }
      });

      window.addEventListener("mouseleave", () => {
        isInsideRock = false;
        triggerReassemble();
        targetLeanX = 0;
        targetLeanY = 0;
      });

      canvasFrame.addEventListener("click", () => {
        if (isShatteredState) {
          // If dream portal is open, clicking it triggers dream mode!
          const dreamBtn = document.getElementById("fixed-theme-btn");
          if (dreamBtn) dreamBtn.click();
          triggerReassemble();
        } else {
          triggerShatter(1.8);
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
        if (crystalMat && crystalMat.uniforms) {
          crystalMat.uniforms.uNight.value = isDream ? 1.0 : 0.0;
        }
        updateBackTexture(isDream);
        if (pMat) pMat.color.setHex(isDream ? 0xe879f9 : 0x93c5fd);
        if (dirLight1) dirLight1.color.setHex(0xffffff);
        if (dirLight2) dirLight2.color.setHex(isDream ? 0xa855f7 : 0xffd166);
        if (dirLight3) dirLight3.color.setHex(isDream ? 0x00f0ff : 0x38bdf8);
      };

      window.syncThreePalette(document.documentElement.classList.contains("dream-mode"));

      window.addEventListener("resize", () => {
        if (!canvasFrame || !renderer || !camera) return;
        const w = canvasFrame.clientWidth || window.innerWidth;
        const h = canvasFrame.clientHeight || window.innerHeight;
        if (w > 0 && h > 0) {
          camera.aspect = w / h;
          camera.updateProjectionMatrix();
          renderer.setSize(w, h);
        }
        updateRockPlacement();
        updateBackTexture(document.documentElement.classList.contains("dream-mode"));
      });

      const clock = new THREE.Clock();

      function animateThree() {
        requestAnimationFrame(animateThree);
        if (prefersReducedMotion) {
          renderer.render(scene, camera);
          return;
        }

        const elapsed = clock.getElapsedTime();
        const dt = Math.min(clock.getDelta(), 0.04);

        if (crystalMat && crystalMat.uniforms) {
          crystalMat.uniforms.uTime.value = elapsed;

          // Smooth transition of crystal material form color & intensity
          const curForm = CRYSTAL_FORMS[currentFormIndex];
          if (curForm) {
            crystalMat.uniforms.uFormColor.value.lerp(curForm.color, dt * 6.0);
            const targetIntensity = (curForm.id === "quartz") ? 0.0 : curForm.intensity;
            crystalMat.uniforms.uFormIntensity.value += (targetIntensity - crystalMat.uniforms.uFormIntensity.value) * (dt * 6.0);
          }
        }

        // Scale active 3D emblem up in center, scale others down
        const curForm = CRYSTAL_FORMS[currentFormIndex];
        if (curForm) {
          for (let key in emblemMeshes) {
            const m = emblemMeshes[key];
            const isTarget = (key === curForm.emblem && !isShatteredState);
            const targetS = isTarget ? 1.0 : 0.0;
            m.scale.lerp(new THREE.Vector3(targetS, targetS, targetS), dt * 9.0);
            m.rotation.y += dt * 0.8;
          }
        }

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
          pixelBadgeMesh.position.y = 1.30 + Math.sin(elapsed * 2.2) * 0.04;
        }

        // Portal scale lerp
        const targetPScale = isShatteredState ? 1.05 : 0.0;
        portalScale += (targetPScale - portalScale) * (isShatteredState ? 0.08 : 0.12);
        if (portalScale < 0.005) portalScale = 0.0;
        if (portalGroup) {
          portalGroup.scale.set(portalScale, portalScale, portalScale);
          portalGroup.rotation.z = elapsed * 0.22;
        }
        if (portalLight) {
          portalLight.intensity = portalScale * 4.5;
        }

        // Full-screen zero-g physics simulation for all solid crystal chunks
        for (let i = 0; i < shardData.length; i++) {
          const s = shardData[i];
          if (!s || !s.mesh) continue;

          if (!isShatteredState) {
            // REASSEMBLING: Strong Magnetic Spring with Critical Damping
            const targetPos = s.formPos || s.centroid;
            const toTarget = new THREE.Vector3().subVectors(targetPos, s.currPos);
            const dist = toTarget.length();

            if (dist > 0.015) {
              const springF = toTarget.clone().multiplyScalar(52.0); // Fast magnetic pull
              s.velocity.addScaledVector(springF, dt);
              s.velocity.multiplyScalar(Math.exp(-dt * 10.5)); // Critical damping
              s.currPos.addScaledVector(s.velocity, dt);

              // Smoothly orient back to form alignment
              s.currQuat.slerp(s.homeQuat, dt * 14.0);
            } else {
              s.currPos.copy(targetPos);
              s.currQuat.copy(s.homeQuat);
              s.velocity.set(0, 0, 0);
              s.angVel.set(0, 0, 0);
            }
          } else {
            // SHATTERED: Space drag + Harmonic orbital drift
            const targetPos = s.centroid.clone().addScaledVector(s.scatterDir, s.scatterDist);
            const toTarget = new THREE.Vector3().subVectors(targetPos, s.currPos);

            // Guidance acceleration towards scattered zero-g orbit
            s.velocity.addScaledVector(toTarget, dt * 3.5);
            s.velocity.multiplyScalar(Math.exp(-dt * 2.2)); // Space drag

            // Micro harmonic orbital drift
            const driftX = Math.sin(elapsed * s.driftSpeed + s.driftPhase) * 0.008;
            const driftY = Math.cos(elapsed * s.driftSpeed * 0.8 + s.driftPhase) * 0.008;
            const driftZ = Math.sin(elapsed * s.driftSpeed * 1.2 + s.driftPhase) * 0.008;
            s.currPos.x += s.velocity.x * dt + driftX;
            s.currPos.y += s.velocity.y * dt + driftY;
            s.currPos.z += s.velocity.z * dt + driftZ;

            // 3D rotation tumbling
            const spinAmount = Math.max(s.angVel.length(), 0.35) * dt;
            const deltaRot = new THREE.Quaternion().setFromAxisAngle(s.tumbleAxis, spinAmount);
            s.currQuat.multiply(deltaRot);
            s.angVel.multiplyScalar(Math.exp(-dt * 0.8));
          }

          s.mesh.position.copy(s.currPos);
          s.mesh.quaternion.copy(s.currQuat);
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
  if (window.location.search.includes("dream")) {
    setMode("dream");
  } else if (isDreamActive()) {
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
