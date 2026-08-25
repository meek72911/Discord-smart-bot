/* ============================================================
   SMART BOT — Interactive State Engine
   Sakura petal sky · neural sparkline · count-ups · nav
   ============================================================ */

/* ---------- Sakura petal + star sky ---------- */
const sky = document.getElementById("sky");
const sctx = sky.getContext("2d");
let W, H;
function resize() {
  W = sky.width = innerWidth * devicePixelRatio;
  H = sky.height = innerHeight * devicePixelRatio;
  sky.style.width = innerWidth + "px";
  sky.style.height = innerHeight + "px";
}
resize();
addEventListener("resize", resize);

const PETAL_COLORS = [
  ["#ff7ab8", "#ff2d78"],
  ["#ffb3d4", "#ff5c9d"],
  ["#e9a8ff", "#b829ff"],
  ["#ff9ec9", "#e033ff"],
];
const petals = [];
const PETAL_COUNT = Math.min(34, Math.floor(innerWidth / 42));
for (let i = 0; i < PETAL_COUNT; i++) petals.push(newPetal(true));

function newPetal(anywhere) {
  const c = PETAL_COLORS[(Math.random() * PETAL_COLORS.length) | 0];
  return {
    x: Math.random() * W,
    y: anywhere ? Math.random() * H : -30 * devicePixelRatio,
    s: (5 + Math.random() * 9) * devicePixelRatio,
    vy: (0.35 + Math.random() * 0.75) * devicePixelRatio,
    sway: 18 + Math.random() * 34 * devicePixelRatio,
    phase: Math.random() * Math.PI * 2,
    spin: (Math.random() - 0.5) * 0.02,
    a: Math.random() * Math.PI,
    c0: c[0], c1: c[1],
    alpha: 0.35 + Math.random() * 0.5,
  };
}

const stars = [];
const STAR_COUNT = Math.min(90, Math.floor(innerWidth / 14));
for (let i = 0; i < STAR_COUNT; i++) {
  stars.push({
    x: Math.random(), y: Math.random(),
    r: (0.4 + Math.random() * 1.3) * devicePixelRatio,
    p: Math.random() * Math.PI * 2,
    sp: 0.4 + Math.random() * 1.2,
  });
}

function drawPetal(p) {
  sctx.save();
  sctx.translate(p.x, p.y);
  sctx.rotate(p.a);
  const g = sctx.createLinearGradient(-p.s, -p.s, p.s, p.s);
  g.addColorStop(0, p.c0);
  g.addColorStop(1, p.c1);
  sctx.fillStyle = g;
  sctx.globalAlpha = p.alpha;
  sctx.beginPath();
  // sakura petal: teardrop with notch
  sctx.moveTo(0, -p.s);
  sctx.bezierCurveTo(p.s * 0.9, -p.s * 0.6, p.s * 0.75, p.s * 0.7, 0, p.s);
  sctx.bezierCurveTo(-p.s * 0.75, p.s * 0.7, -p.s * 0.9, -p.s * 0.6, 0, -p.s);
  // notch
  sctx.globalCompositeOperation = "destination-out";
  sctx.beginPath();
  sctx.arc(0, -p.s * 0.92, p.s * 0.22, 0, Math.PI * 2);
  sctx.fill();
  sctx.globalCompositeOperation = "source-over";
  sctx.fill();
  sctx.restore();
}

let t = 0;
function frame() {
  t += 0.016;
  sctx.clearRect(0, 0, W, H);

  // twinkling stars
  for (const s of stars) {
    const tw = 0.35 + 0.65 * Math.abs(Math.sin(t * s.sp + s.p));
    sctx.globalAlpha = tw * 0.8;
    sctx.fillStyle = "#ffd7ea";
    sctx.beginPath();
    sctx.arc(s.x * W, s.y * H, s.r, 0, Math.PI * 2);
    sctx.fill();
  }
  sctx.globalAlpha = 1;

  // falling petals
  for (let i = 0; i < petals.length; i++) {
    const p = petals[i];
    p.y += p.vy;
    p.x += Math.sin(t * 0.8 + p.phase) * (p.sway * 0.012);
    p.a += p.spin;
    if (p.y > H + 40) petals[i] = newPetal(false);
    drawPetal(p);
  }
  requestAnimationFrame(frame);
}
frame();

/* ---------- Health gauge animation ---------- */
const arc = document.querySelector(".gauge-arc");
if (arc) {
  const target = 213.6 * (1 - 0.78);
  const obs = new IntersectionObserver((es) => {
    es.forEach((e) => {
      if (e.isIntersecting) {
        setTimeout(() => (arc.style.strokeDashoffset = target), 350);
        obs.disconnect();
      }
    });
  });
  obs.observe(arc);
}

/* ---------- Count-up numbers ---------- */
const counters = document.querySelectorAll(".count");
const cObs = new IntersectionObserver((es) => {
  es.forEach((e) => {
    if (!e.isIntersecting) return;
    const el = e.target;
    cObs.unobserve(el);
    const target = parseFloat(el.dataset.target);
    const suffix = el.dataset.suffix || "";
    const dec = target % 1 !== 0 ? 1 : 0;
    const start = performance.now();
    const dur = 1400;
    function tick(now) {
      const p = Math.min(1, (now - start) / dur);
      const eased = 1 - Math.pow(1 - p, 3);
      el.textContent = (target * eased).toFixed(dec) + suffix;
      if (p < 1) requestAnimationFrame(tick);
    }
    requestAnimationFrame(tick);
  });
});
counters.forEach((c) => cObs.observe(c));

/* ---------- Footer sparkline ---------- */
const spark = document.getElementById("spark");
if (spark) {
  const ctx = spark.getContext("2d");
  const w = spark.width, h = spark.height;
  const pts = [];
  for (let i = 0; i < 40; i++) pts.push(0.5 + Math.sin(i * 0.55) * 0.16 + Math.random() * 0.14);
  let shift = 0;
  function drawSpark() {
    ctx.clearRect(0, 0, w, h);
    ctx.beginPath();
    for (let i = 0; i < pts.length; i++) {
      const idx = (i + shift) % pts.length;
      const x = (i / (pts.length - 1)) * w;
      const y = h - pts[idx] * h;
      i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
    }
    ctx.strokeStyle = "#4ade80";
    ctx.lineWidth = 1.6;
    ctx.shadowColor = "#4ade80";
    ctx.shadowBlur = 7;
    ctx.stroke();
    shift = (shift + 1) % pts.length;
  }
  drawSpark();
  setInterval(drawSpark, 900);
}

/* ---------- Mobile nav ---------- */
const burger = document.getElementById("hamburger");
const links = document.getElementById("navLinks");
if (burger) {
  burger.addEventListener("click", () => links.classList.toggle("open"));
  links.querySelectorAll("a").forEach((a) =>
    a.addEventListener("click", () => links.classList.remove("open"))
  );
}

/* ---------- Demo buttons -> toast ---------- */
const toast = document.getElementById("toast");
function showToast(msg) {
  toast.textContent = msg;
  toast.classList.add("show");
  setTimeout(() => toast.classList.remove("show"), 2400);
}
document.querySelectorAll(".action-row .btn").forEach((b) => {
  b.addEventListener("click", () =>
    showToast(b.textContent.trim() === "Run Auto-Clean"
      ? "🧹 Auto-clean executed — 42 spam messages purged!"
      : "👌 Noted — auto-clean skipped.")
  );
});
const demoBtn = document.querySelector(".btn-ghost.btn-big");
if (demoBtn) demoBtn.addEventListener("click", (e) => {
  e.preventDefault();
  document.querySelector(".discord").scrollIntoView({ behavior: "smooth", block: "center" });
  showToast("🎬 Live demo — this is the real interface!");
});

/* ---------- Nav scroll shadow ---------- */
addEventListener("scroll", () => {
  document.querySelector(".nav").style.boxShadow =
    scrollY > 30 ? "0 10px 44px rgba(255,45,120,.16)" : "none";
});

/* ---------- Live Gateway Pulse (Keep-Alive Sentinel) ---------- */
async function pulseGateway() {
  try {
    const res = await fetch('/api/keep-alive');
    const data = await res.json();
    console.log('[SmartBot Sentinel] Gateway Pulse:', data.status, `${data.latency_ms}ms`);
  } catch (err) {
    fetch('https://smart-bot-discord-engine.onrender.com', { mode: 'no-cors' }).catch(() => {});
  }
}
pulseGateway();
setInterval(pulseGateway, 60000);
