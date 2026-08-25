/* ==========================================================================
   SMART BOT OS — PRO CLIENT SCRIPT
   Linear × Vercel × Discord × Sakura Motion Intelligence
   ========================================================================== */

// 1. Lenis Smooth Inertia Scroll + GSAP Sync
let lenis = null;
const prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

if (!prefersReduced && typeof Lenis !== 'undefined') {
  lenis = new Lenis({
    duration: 1.2,
    easing: (t) => Math.min(1, 1.001 - Math.pow(2, -10 * t)),
    smoothTouch: false,
  });

  if (typeof gsap !== 'undefined' && typeof ScrollTrigger !== 'undefined') {
    gsap.registerPlugin(ScrollTrigger);
    lenis.on('scroll', ScrollTrigger.update);
    gsap.ticker.add((time) => {
      lenis.raf(time * 1000);
    });
    gsap.ticker.lagSmoothing(0);
  } else {
    function raf(time) {
      lenis.raf(time);
      requestAnimationFrame(raf);
    }
    requestAnimationFrame(raf);
  }
}

// 2. Micro-Interactions & Scroll Animations
document.addEventListener('DOMContentLoaded', () => {
  initParticleCanvas();
  initHealthGauge();
});

// 3. Ambient Particle Physics (Restrained & Edge-focused)
function initParticleCanvas() {
  const canvas = document.getElementById('bg-canvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');

  let W = (canvas.width = window.innerWidth);
  let H = (canvas.height = window.innerHeight);

  window.addEventListener('resize', () => {
    W = canvas.width = window.innerWidth;
    H = canvas.height = window.innerHeight;
  });

  const PETAL_COUNT = W < 768 ? 10 : 20;
  const STAR_COUNT = W < 768 ? 15 : 30;

  const petals = [];
  for (let i = 0; i < PETAL_COUNT; i++) {
    petals.push({
      x: Math.random() * W,
      y: Math.random() * H,
      r: Math.random() * 4 + 2.5,
      vy: Math.random() * 0.5 + 0.25,
      vx: Math.sin(Math.random() * Math.PI) * 0.4,
      rot: Math.random() * 360,
      spin: (Math.random() - 0.5) * 0.015,
      opacity: Math.random() * 0.35 + 0.15,
      color: 'rgba(255, 183, 213, ',
    });
  }

  const stars = [];
  for (let i = 0; i < STAR_COUNT; i++) {
    stars.push({
      x: Math.random() * W,
      y: Math.random() * H,
      r: Math.random() * 1.2 + 0.4,
      alpha: Math.random() * 0.4 + 0.1,
      speed: Math.random() * 0.015 + 0.005,
    });
  }

  function drawPetal(p) {
    ctx.save();
    ctx.translate(p.x, p.y);
    ctx.rotate(p.rot);
    ctx.fillStyle = p.color + p.opacity + ')';
    ctx.beginPath();
    ctx.moveTo(0, -p.r);
    ctx.bezierCurveTo(p.r * 0.8, -p.r * 0.8, p.r * 0.8, p.r * 0.8, 0, p.r * 1.2);
    ctx.bezierCurveTo(-p.r * 0.8, p.r * 0.8, -p.r * 0.8, -p.r * 0.8, 0, -p.r);
    ctx.fill();
    ctx.restore();
  }

  let t = 0;
  function loop() {
    ctx.clearRect(0, 0, W, H);
    t += 0.008;

    // Ambient stars
    ctx.fillStyle = '#ffffff';
    for (let s of stars) {
      s.alpha += Math.sin(t * 2 + s.x) * s.speed;
      ctx.globalAlpha = Math.max(0.08, Math.min(0.5, s.alpha));
      ctx.beginPath();
      ctx.arc(s.x, s.y, s.r, 0, Math.PI * 2);
      ctx.fill();
    }

    // Drifting Sakura Petals
    for (let p of petals) {
      p.y += p.vy;
      p.x += Math.sin(t + p.y * 0.008) * 0.4;
      p.rot += p.spin;

      if (p.y > H + 20) {
        p.y = -20;
        p.x = Math.random() * W;
      }
      if (p.x > W + 20) p.x = -20;
      if (p.x < -20) p.x = W + 20;

      drawPetal(p);
    }
    ctx.globalAlpha = 1;
    requestAnimationFrame(loop);
  }
  loop();
}

// 4. Section 01 — Community Health Gauge Animation (0 -> 92)
function initHealthGauge() {
  const arc = document.getElementById('health-arc');
  const numEl = document.getElementById('health-num');
  if (!arc || !numEl) return;

  const targetScore = 92;
  const maxDash = 283; // 2 * PI * 45
  const offset = maxDash - (maxDash * targetScore) / 100;

  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          setTimeout(() => {
            arc.style.strokeDashoffset = offset;
            
            // Count up 0 -> 92
            let current = 0;
            const duration = 1200;
            const stepTime = duration / targetScore;
            const timer = setInterval(() => {
              current++;
              numEl.textContent = current;
              if (current >= targetScore) {
                clearInterval(timer);
              }
            }, stepTime);

          }, 200);
          observer.disconnect();
        }
      });
    },
    { threshold: 0.3 }
  );
  observer.observe(arc);
}

// 5. Interactive Command Snippet Copy
function copySnippet(cmd) {
  navigator.clipboard.writeText(cmd).then(() => {
    alert(`Copied "${cmd}" to clipboard! Paste it into Discord.`);
  });
}
