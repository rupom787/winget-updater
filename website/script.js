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
  // 13. AERODYNAMIC BLUE WIND MOUSE TRAIL STREAM
  // ==========================================
  function initWindCursor() {
    const canvas = document.getElementById("wind-stream-canvas");
    if (!canvas || !window.matchMedia("(pointer: fine)").matches) return;

    const ctx = canvas.getContext("2d");
    let width = 0, height = 0, dpr = 1;

    function resize() {
      dpr = Math.min(window.devicePixelRatio || 1, 2);
      width = window.innerWidth;
      height = window.innerHeight;
      canvas.width = Math.floor(width * dpr);
      canvas.height = Math.floor(height * dpr);
      canvas.style.width = width + "px";
      canvas.style.height = height + "px";
      ctx.setTransform(1, 0, 0, 1, 0, 0);
      ctx.scale(dpr, dpr);
    }
    resize();
    window.addEventListener("resize", resize);

    const points = [];
    const particles = [];
    const MAX_POINTS = 38;
    let lastX = 0, lastY = 0, lastTime = performance.now();
    let hasMoved = false;

    window.addEventListener("mousemove", (e) => {
      const now = performance.now();
      const dt = Math.max((now - lastTime) / 1000, 0.001);
      const vx = (e.clientX - lastX) / dt;
      const vy = (e.clientY - lastY) / dt;
      const speed = Math.hypot(vx, vy);

      lastX = e.clientX;
      lastY = e.clientY;
      lastTime = now;

      if (!hasMoved) {
        hasMoved = true;
        return;
      }

      // Emit aerodynamic wind flow when moving
      if (speed > 18) {
        const len = speed || 1;
        const nx = -vy / len;
        const ny = vx / len;

        points.push({
          x: e.clientX,
          y: e.clientY,
          vx: vx * 0.08,
          vy: vy * 0.08,
          nx: nx,
          ny: ny,
          speed: speed,
          age: 0,
          maxAge: Math.min(0.40 + speed * 0.00035, 0.68),
          width: Math.min(2.0 + speed * 0.0045, 5.2),
        });

        if (points.length > MAX_POINTS) points.shift();

        // Release delicate glowing wind motes in the aerodynamic wake
        if (speed > 160 && Math.random() < 0.7) {
          const side = (Math.random() - 0.5) * 14;
          particles.push({
            x: e.clientX + nx * side,
            y: e.clientY + ny * side,
            vx: vx * 0.03 + (Math.random() - 0.5) * 20,
            vy: vy * 0.03 - 12 - Math.random() * 18, // buoyant upward air drift
            size: 1.2 + Math.random() * 2.0,
            age: 0,
            maxAge: 0.35 + Math.random() * 0.35,
          });
        }
      }
    });

    let lastFrame = performance.now();

    function renderWind(now) {
      requestAnimationFrame(renderWind);
      const dt = Math.min((now - lastFrame) / 1000, 0.05);
      lastFrame = now;

      if (points.length === 0 && particles.length === 0) {
        return;
      }

      ctx.clearRect(0, 0, width, height);

      const isDream = document.documentElement.classList.contains("dream-mode");
      ctx.globalCompositeOperation = isDream ? "lighter" : "source-over";

      // Age points and apply atmospheric drag + buoyant breeze drift
      for (let i = points.length - 1; i >= 0; i--) {
        const p = points[i];
        p.age += dt;
        p.x += p.vx * dt;
        p.y += p.vy * dt - 10 * dt; // gentle rising breeze
        p.vx *= Math.exp(-dt * 3.2);
        p.vy *= Math.exp(-dt * 3.2);
        if (p.age >= p.maxAge) {
          points.splice(i, 1);
        }
      }

      // Draw 3 interlaced aerodynamic blue wind filaments
      if (points.length > 2) {
        const strands = [
          { offsetMul: 0,    alphaMul: 1.0,  widthMul: 1.0,  hue: isDream ? "#38bdf8" : "#0284c7" },
          { offsetMul: 6.5,  alphaMul: 0.65, widthMul: 0.65, hue: isDream ? "#60a5fa" : "#38bdf8" },
          { offsetMul: -6.0, alphaMul: 0.55, widthMul: 0.55, hue: isDream ? "#93c5fd" : "#0ea5e9" },
        ];

        for (const strand of strands) {
          for (let i = 0; i < points.length - 1; i++) {
            const p1 = points[i];
            const p2 = points[i + 1];

            const t = now * 0.007 + i * 0.38;
            const curl = Math.sin(t) * strand.offsetMul;

            const x1 = p1.x + p1.nx * curl;
            const y1 = p1.y + p1.ny * curl;
            const x2 = p2.x + p2.nx * curl;
            const y2 = p2.y + p2.ny * curl;

            const life = 1.0 - (p2.age / p2.maxAge);
            const alpha = Math.max(life, 0) * (isDream ? 0.80 : 0.85) * strand.alphaMul;
            const strokeW = Math.max(p2.width * life * strand.widthMul, 0.5);

            ctx.beginPath();
            ctx.moveTo(x1, y1);
            const mx = (x1 + x2) * 0.5;
            const my = (y1 + y2) * 0.5;
            ctx.quadraticCurveTo(x1, y1, mx, my);

            ctx.strokeStyle = strand.hue;
            ctx.globalAlpha = alpha;
            ctx.lineWidth = strokeW;
            ctx.lineCap = "round";
            ctx.lineJoin = "round";
            ctx.stroke();
          }
        }
      }

      // Render micro luminous blue air dust particles
      for (let i = particles.length - 1; i >= 0; i--) {
        const pt = particles[i];
        pt.age += dt;
        pt.x += pt.vx * dt;
        pt.y += pt.vy * dt;
        pt.vx *= Math.exp(-dt * 2.8);
        pt.vy *= Math.exp(-dt * 2.8);

        const life = 1.0 - (pt.age / pt.maxAge);
        if (life <= 0) {
          particles.splice(i, 1);
          continue;
        }

        const pAlpha = life * (isDream ? 0.85 : 0.75);
        ctx.beginPath();
        ctx.arc(pt.x, pt.y, pt.size * life, 0, Math.PI * 2);
        ctx.fillStyle = isDream ? "#e0f2fe" : "#0284c7";
        ctx.globalAlpha = pAlpha;
        ctx.fill();
      }

      ctx.globalAlpha = 1.0;
    }

    requestAnimationFrame(renderWind);
  }
  initWindCursor();

  // ==========================================
  // 14. THREE.JS DAIKI FUJITA ORGANIC CRYSTAL ROCK WITH COSMIC DREAM PORTAL
  // ==========================================
  const canvas = document.getElementById("hero-webgl-canvas");
  const canvasFrame = document.getElementById("canvas-frame");
  const gemStatusEl = document.getElementById("telemetry-gem-status");
  const gemHintEl = document.getElementById("telemetry-gem-hint");

  let rockGroup, shardMeshes = [], shardData = [], portalGroup, portalLight, causticMesh;
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
        } else if (w > 768) {
          rockGroup.position.set(0.65, -0.1, 0);
          if (causticMesh) causticMesh.position.set(0.65, -1.6, -0.2);
        } else {
          rockGroup.position.set(0, -0.55, 0);
          if (causticMesh) causticMesh.position.set(0, -2.1, -0.2);
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

        // Concentric Luminous Ripple Rings (Pure Celestial Starlight)
        ctx.strokeStyle = "rgba(224, 242, 254, 0.75)";
        ctx.lineWidth = 2.5;
        ctx.beginPath();
        ctx.arc(size / 2, size / 2, size * 0.35, 0, Math.PI * 2);
        ctx.stroke();

        ctx.strokeStyle = "rgba(186, 230, 253, 0.45)";
        ctx.lineWidth = 1.8;
        ctx.beginPath();
        ctx.arc(size / 2, size / 2, size * 0.22, 0, Math.PI * 2);
        ctx.stroke();

        // Center Pulsing Orb (Pure Diamond Core)
        const centerGrad = ctx.createRadialGradient(size / 2, size / 2, 0, size / 2, size / 2, size * 0.12);
        centerGrad.addColorStop(0, "rgba(255, 255, 255, 1)");
        centerGrad.addColorStop(0.4, "rgba(240, 249, 255, 0.85)");
        centerGrad.addColorStop(1, "rgba(186, 230, 253, 0)");
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
        ctx.shadowColor = "rgba(255, 255, 255, 0.8)";
        ctx.shadowBlur = 10;
        ctx.fillText("ENTER", size / 2, size / 2 - 16);
        ctx.font = "bold 24px 'Space Grotesk', -apple-system, sans-serif";
        ctx.fillText("THE DREAM", size / 2, size / 2 + 18);

        return new THREE.CanvasTexture(pCanvas);
      }

      // C. Pure Quartz Caustic Floor Light Pool
      function createCausticTexture() {
        const cCanvas = document.createElement("canvas");
        cCanvas.width = 512;
        cCanvas.height = 512;
        const ctx = cCanvas.getContext("2d");
        const grad = ctx.createRadialGradient(256, 256, 10, 256, 256, 250);
        grad.addColorStop(0, "rgba(240, 248, 255, 0.32)");
        grad.addColorStop(0.35, "rgba(224, 242, 254, 0.14)");
        grad.addColorStop(0.7, "rgba(200, 230, 255, 0.03)");
        grad.addColorStop(1, "rgba(200, 230, 255, 0)");
        ctx.fillStyle = grad;
        ctx.beginPath();
        ctx.arc(256, 256, 250, 0, Math.PI * 2);
        ctx.fill();
        return new THREE.CanvasTexture(cCanvas);
      }

      // --- 2. LUXURY STUDIO LIGHTING (PURE OPTICAL WHITE & SILVER) ---
      const ambientLight = new THREE.AmbientLight(0xffffff, 1.4);
      scene.add(ambientLight);

      dirLight1 = new THREE.DirectionalLight(0xffffff, 5.2); // Crisp diamond specular key
      dirLight1.position.set(5, 7, 5);
      scene.add(dirLight1);

      dirLight2 = new THREE.DirectionalLight(0xf1f5f9, 3.2); // Soft silver bounce fill
      dirLight2.position.set(-6, 3, -4);
      scene.add(dirLight2);

      dirLight3 = new THREE.DirectionalLight(0xe2e8f0, 2.8); // Pure chiseled facet edge rim
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

      // Note: Orbiting cylinder circle & pixel badge removed per user request for pure monolithic quartz elegance

      updateRockPlacement();

      // --- 4. CELESTIAL ZERO-G GRAVITATIONAL SINGULARITY (SILVER / WHITE) ---
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

      portalLight = new THREE.PointLight(0xffffff, 0, 8);
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

        void main() {
          vec2 screenUv = (vScreenPos.xy / vScreenPos.w) * 0.5 + 0.5;

          vec3 V = normalize(vViewPosition);
          vec3 N = normalize(vNormal);

          // Fine raw chiseled facet micro-surface normals
          vec2 normUv = vWorldPosition.xy * 0.40 + vWorldPosition.z * 0.14;
          vec3 normalTex = texture2D(tNormal, normUv).rgb * 2.0 - 1.0;
          N = normalize(N + normalTex * 0.26);

          float NdotV = clamp(dot(N, V), 0.0, 1.0);

          // Physical Quartz / Diamond Fresnel (F0 = 0.055, rising to 1.0 at grazing angles)
          float f0 = 0.055;
          float fresnel = f0 + (1.0 - f0) * pow(1.0 - NdotV, 3.6);

          // Physical optical refraction offset
          vec2 refractOffset = vec2(-N.x, N.y) * (uRefract * 0.90);

          // Subtle physical chromatic dispersion (delicate optical glass, zero synthetic rainbow)
          float disp = uDisp * 0.40;
          float r = texture2D(tBack, clamp(screenUv + refractOffset * (1.0 + disp), 0.001, 0.999)).r;
          float g = texture2D(tBack, clamp(screenUv + refractOffset, 0.001, 0.999)).g;
          float b = texture2D(tBack, clamp(screenUv + refractOffset * (1.0 - disp), 0.001, 0.999)).b;
          vec3 refractedColor = vec3(r, g, b);

          // Internal mineral cleavage depth and suspended light fractures
          vec4 internalCleavage = texture2D(tMatcap, normUv * 0.70 + vec2(uTime * 0.008, 0.0));

          // Triple studio specular glints for crystalline brilliance:
          // Key Light: intense diamond sparkle
          vec3 light1 = normalize(vec3(0.55, 0.80, 0.60));
          vec3 H1 = normalize(light1 + V);
          float spec1 = pow(max(dot(N, H1), 0.0), 90.0) * 2.8;

          // Fill Light: faceted edge definition
          vec3 light2 = normalize(vec3(-0.65, 0.35, 0.40));
          vec3 H2 = normalize(light2 + V);
          float spec2 = pow(max(dot(N, H2), 0.0), 45.0) * 1.2;

          // Back Rim Kicker: razor-sharp silhouette glint
          vec3 light3 = normalize(vec3(0.15, -0.65, -0.60));
          vec3 H3 = normalize(light3 + V);
          float spec3 = pow(max(dot(N, H3), 0.0), 32.0) * 0.95;

          // Mode-aware crystal facet contrast:
          // In Light/Wake mode (uNight = 0): chiseled graphite facet edges & ambient refraction outline the 3D rock
          // In Dark/Dream mode (uNight = 1): brilliant silver/white specular rim reflection against deep space
          vec3 edgeColor = mix(vec3(0.18, 0.22, 0.28), vec3(0.96, 0.98, 1.0), uNight);
          vec3 coreTint = mix(vec3(0.88, 0.90, 0.93), vec3(0.96, 0.98, 1.0), uNight);
          vec3 quartzTint = mix(coreTint, edgeColor, fresnel);

          // Composite: pristine high-transmittance crystal volume with razor facet definition
          vec3 col = mix(refractedColor, quartzTint, mix(0.35, 0.18, uNight));
          col += internalCleavage.rgb * (0.045 + (1.0 - uNight) * 0.035);
          col += vec3(1.0) * (spec1 + spec2 + spec3); // Diamond specular glints gleam brilliantly in all modes
          col += edgeColor * fresnel * mix(0.38, 0.52, uNight);

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
        },
        transparent: true,
        side: THREE.DoubleSide,
      });

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

      // --- 8. PHYSICS, MOUSE SHATTER & REASSEMBLE CONTROLLER ---
      let isShatteredState = false;
      let isReassembling = false;
      let reassembleTimer = null;
      let portalScale = 0.0;
      let targetLeanX = 0, targetLeanY = 0;
      let isDragging = false;
      let previousPointerX = 0, previousPointerY = 0;
      let dragVelocityX = 0, dragVelocityY = 0;

      if (window.location.search.includes("shatter")) {
        isShatteredState = true;
      }

      function triggerShatter(impulseStrength = 1.0) {
        if (!isShatteredState) {
          isShatteredState = true;
          isReassembling = false;
          if (reassembleTimer) {
            clearTimeout(reassembleTimer);
            reassembleTimer = null;
          }
          if (audio) {
            audio.playCrystalShatter();
            if (audio.playBlip) {
              audio.playBlip(2800, 0.04, 0.08);
              setTimeout(() => audio.playBlip(1600, 0.08, 0.06), 35);
            }
          }
          if (gemStatusEl) gemStatusEl.textContent = "COSMIC PURPLE DREAM PORTAL [FRACTURED]";
          if (gemHintEl) gemHintEl.textContent = "SHATTERED — MAGNETIC REASSEMBLY ARMED";

          // Inject initial kinetic impulse into all solid shards
          const strength = Math.min(Math.max(impulseStrength, 0.8), 2.5);
          for (let i = 0; i < shardData.length; i++) {
            const s = shardData[i];
            const impulse = (s.scatterDist * 2.8 * strength) / s.mass;
            s.velocity.copy(s.scatterDir).multiplyScalar(impulse);
            s.angVel.copy(s.tumbleAxis).multiplyScalar(s.tumbleSpeed * 2.2 * strength);
          }

          // Automatically reassemble after 2.8 seconds so it always comes back together and fixes itself!
          reassembleTimer = setTimeout(() => {
            triggerReassemble();
          }, 2800);
        }
      }

      function triggerReassemble() {
        if (reassembleTimer) {
          clearTimeout(reassembleTimer);
          reassembleTimer = null;
        }
        if (isShatteredState) {
          isShatteredState = false;
          isReassembling = true;
          if (audio) {
            audio.playCrystalReassemble();
            if (audio.playBlip) audio.playBlip(1200, 0.04, 0.05);
          }
          if (gemStatusEl) gemStatusEl.textContent = "QUARTZ CRYSTAL ROCK [REASSEMBLING]";
          if (gemHintEl) gemHintEl.textContent = "MAGNETIC REASSEMBLY IN PROGRESS";
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
          const rockScreenRadius = Math.min(w, h) * (w > 768 ? 0.22 : 0.32);

          // Physical break trigger: cursor strikes or moves into the rock!
          if (distToRock < rockScreenRadius) {
            if (!isInsideRock && !isReassembling) {
              isInsideRock = true;
              const impact = 1.0 + Math.min(cursorSpeed / 1200, 1.2);
              triggerShatter(impact);
            }
          } else if (distToRock > rockScreenRadius * 1.08) {
            // Reassemble trigger: cursor moves away from rock zone
            isInsideRock = false;
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

      const telemetryBox = document.querySelector(".canvas-telemetry-fullscreen");
      if (telemetryBox) {
        telemetryBox.style.cursor = "pointer";
        telemetryBox.title = "Click to toggle crystal shatter or reassemble";
        telemetryBox.addEventListener("click", (e) => {
          e.stopPropagation();
          if (isShatteredState) {
            triggerReassemble();
          } else {
            triggerShatter(1.8);
          }
        });
      }

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
        if (pMat) pMat.color.setHex(isDream ? 0xe2e8f0 : 0x94a3b8);
        if (dirLight1) dirLight1.color.setHex(0xffffff);
        if (dirLight2) dirLight2.color.setHex(0xf1f5f9);
        if (dirLight3) dirLight3.color.setHex(0xe2e8f0);
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

      let lastFrameTime = performance.now();
      const animationStartTime = performance.now();

      function animateThree() {
        requestAnimationFrame(animateThree);
        if (prefersReducedMotion) {
          renderer.render(scene, camera);
          return;
        }

        const now = performance.now();
        // Reliable frame delta time (independent of THREE.Clock side effects)
        const dt = Math.min(Math.max((now - lastFrameTime) / 1000, 0.001), 0.05);
        lastFrameTime = now;
        const elapsed = (now - animationStartTime) / 1000;

        if (crystalMat && crystalMat.uniforms) {
          crystalMat.uniforms.uTime.value = elapsed;
        }

        // Inertia drag damping & idle rock rotation
        if (!isDragging && rockGroup) {
          dragVelocityX *= 0.92;
          dragVelocityY *= 0.92;
          rockGroup.rotation.y += dragVelocityX + 0.005;
          rockGroup.rotation.x += dragVelocityY + 0.002;
        }

// Orbiting typography ring & floating pixel badge removed

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
        let allReassembled = true;
        for (let i = 0; i < shardData.length; i++) {
          const s = shardData[i];
          if (!s || !s.mesh) continue;

          if (!isShatteredState) {
            // REASSEMBLING: Magnetic Damped Harmonic Spring pulling toward centroid
            const toHome = new THREE.Vector3().subVectors(s.centroid, s.currPos);
            const dist = toHome.length();

            if (dist > 0.006) {
              allReassembled = false;
              const springF = toHome.clone().multiplyScalar(36.0);
              s.velocity.addScaledVector(springF, dt);
              s.velocity.multiplyScalar(Math.exp(-dt * 8.0));
              s.currPos.addScaledVector(s.velocity, dt);

              // Smoothly orient back to original crystal facet alignment
              s.currQuat.slerp(s.homeQuat, Math.min(dt * 15.0, 1.0));
            } else {
              s.currPos.copy(s.centroid);
              s.currQuat.copy(s.homeQuat);
              s.velocity.set(0, 0, 0);
              s.angVel.set(0, 0, 0);
            }
          } else {
            allReassembled = false;
            // SHATTERED: Wide 3D dispersion with space drag + harmonic zero-g bobbing
            const targetPos = s.centroid.clone().addScaledVector(s.scatterDir, s.scatterDist);
            const toTarget = new THREE.Vector3().subVectors(targetPos, s.currPos);

            // Guidance acceleration towards scattered zero-g orbit
            s.velocity.addScaledVector(toTarget, dt * 2.8);
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

        if (!isShatteredState) {
          if (allReassembled) {
            isReassembling = false;
            if (gemStatusEl && gemStatusEl.textContent !== "QUARTZ CRYSTAL ROCK [SOLID]") {
              gemStatusEl.textContent = "QUARTZ CRYSTAL ROCK [SOLID]";
            }
            if (gemHintEl && gemHintEl.textContent !== "MOVE CURSOR OVER ROCK TO SHATTER") {
              gemHintEl.textContent = "MOVE CURSOR OVER ROCK TO SHATTER";
            }
          } else {
            if (gemStatusEl && gemStatusEl.textContent !== "QUARTZ CRYSTAL ROCK [REASSEMBLING]") {
              gemStatusEl.textContent = "QUARTZ CRYSTAL ROCK [REASSEMBLING]";
            }
            if (gemHintEl && gemHintEl.textContent !== "MAGNETIC REASSEMBLY IN PROGRESS") {
              gemHintEl.textContent = "MAGNETIC REASSEMBLY IN PROGRESS";
            }
          }
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
      showToast("✓ LAUNCH FILM COMPLETE &bull; GET V2.0.0");
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
