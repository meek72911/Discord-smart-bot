/* =========================================================
   SMART BOT OS — JAVASCRIPT & MOTION INTELLIGENCE ENGINE
   AnimStack v3.0 Standards + Interactive Discord Simulator
   ========================================================= */

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

// 2. GSAP Scroll Animations
document.addEventListener('DOMContentLoaded', () => {
  if (typeof gsap !== 'undefined' && !prefersReduced) {
    // Stagger reveal on Bento Cards
    gsap.from('.glass-card', {
      scrollTrigger: {
        trigger: '.bento-grid',
        start: 'top 80%',
      },
      y: 40,
      opacity: 0,
      duration: 0.8,
      stagger: 0.15,
      ease: 'power3.out',
    });

    // Stagger reveal on Capabilities
    gsap.from('.cap-card', {
      scrollTrigger: {
        trigger: '.cap-grid',
        start: 'top 80%',
      },
      y: 30,
      opacity: 0,
      duration: 0.6,
      stagger: 0.1,
      ease: 'power2.out',
    });
  }

  initParticleCanvas();
  initHealthGauge();
  fetchLiveTelemetry();
});

// 3. Interactive Particle Canvas (Falling Petals + Ambient Stars)
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

  // Mouse spotlight tracking
  let mouse = { x: W / 2, y: H / 2 };
  window.addEventListener('mousemove', (e) => {
    mouse.x = e.clientX;
    mouse.y = e.clientY;
  });

  // Petal & Star Particle Factory
  const PETAL_COUNT = W < 768 ? 14 : 26;
  const STAR_COUNT = W < 768 ? 20 : 45;

  const petals = [];
  for (let i = 0; i < PETAL_COUNT; i++) {
    petals.push({
      x: Math.random() * W,
      y: Math.random() * H,
      r: Math.random() * 5 + 3,
      vy: Math.random() * 0.8 + 0.4,
      vx: Math.sin(Math.random() * Math.PI) * 0.5,
      rot: Math.random() * 360,
      spin: (Math.random() - 0.5) * 0.02,
      opacity: Math.random() * 0.4 + 0.2,
      color: Math.random() > 0.4 ? 'rgba(255, 122, 184, ' : 'rgba(184, 41, 255, ',
    });
  }

  const stars = [];
  for (let i = 0; i < STAR_COUNT; i++) {
    stars.push({
      x: Math.random() * W,
      y: Math.random() * H,
      r: Math.random() * 1.5 + 0.5,
      alpha: Math.random() * 0.5 + 0.2,
      speed: Math.random() * 0.02 + 0.005,
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
    t += 0.01;

    // Ambient stars
    ctx.fillStyle = '#ffffff';
    for (let s of stars) {
      s.alpha += Math.sin(t * 2 + s.x) * s.speed;
      ctx.globalAlpha = Math.max(0.1, Math.min(0.7, s.alpha));
      ctx.beginPath();
      ctx.arc(s.x, s.y, s.r, 0, Math.PI * 2);
      ctx.fill();
    }

    // Floating Petals with soft mouse avoidance
    for (let p of petals) {
      p.y += p.vy;
      p.x += Math.sin(t + p.y * 0.01) * 0.6;
      p.rot += p.spin;

      // Wrap around
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

// 4. Interactive Health Radar SVG Gauge Animation
function initHealthGauge() {
  const arc = document.getElementById('radar-arc');
  if (!arc) return;

  const targetScore = 94;
  const maxDash = 283; // 2 * PI * 45
  const offset = maxDash - (maxDash * targetScore) / 100;

  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          setTimeout(() => {
            arc.style.strokeDashoffset = offset;
          }, 300);
          observer.disconnect();
        }
      });
    },
    { threshold: 0.4 }
  );
  observer.observe(arc);
}

// 5. 1-Click Command Copy
function copyCommand() {
  const text = '/setup';
  navigator.clipboard.writeText(text).then(() => {
    const badge = document.getElementById('copy-badge');
    badge.textContent = 'COPIED!';
    badge.style.background = '#10b981';
    badge.style.color = '#ffffff';

    showToast('✨ Copied /setup to clipboard! Paste it into your Discord server.');

    setTimeout(() => {
      badge.textContent = 'COPY';
      badge.style.background = '';
      badge.style.color = '';
    }, 2400);
  });
}

// 6. Interactive Discord Terminal Simulator
const SIM_RESPONSES = {
  '/health': {
    text: 'Community Health Analysis complete! 📈',
    embed: '<b style="color:#34d399;">📈 Overall Score: 94/100 (Grade A+)</b><br/>• Engagement: <b>Optimal</b> (92%)<br/>• Staff Stability: <b>High</b> (96%)<br/>• Retention: <b>93%</b><br/><i>Recommendation: Server vitality is at peak performance.</i>'
  },
  '/dna': {
    text: 'Server DNA profile generated! 🧬',
    embed: '<b style="color:#ff7ab8;">🧬 Community Archetype:</b> Gaming & Creative Guild<br/>• Communication Tone: <b>Witty, High-Energy</b><br/>• Formality: <b>Casual (Emoji heavy)</b><br/>• Primary Focus: <b>Gaming, Memes & Anime</b>'
  },
  'slap': {
    text: '*winds up a giant squeaky plushie hammer with lightning speed...* 💥 **WHACK!** *Target is sent spinning into the anime stratosphere!* (๑•̀ᗢ•́)و ✨',
    embed: null
  },
  'lock': {
    text: '🛡️ Emergency Channel Protocol Initiated.',
    embed: '<b style="color:#f87171;">🔒 Action:</b> Locked <b>6 channels</b> (Send Messages = False).<br/><i>Audit log notification dispatched to moderators.</i>'
  },
  '/setup': {
    text: '⚙️ Welcome to Smart Bot 60-Second Setup Wizard!',
    embed: '<b>1. Select Mod Log Channel:</b> <mark style="background:rgba(255,45,120,0.2);color:#fff;padding:2px 6px;border-radius:4px;">#mod-audit-log</mark><br/><b>2. AI Personality:</b> <mark style="background:rgba(184,41,255,0.2);color:#fff;padding:2px 6px;border-radius:4px;">Witty / Default</mark><br/><b>3. Confirmation Gates:</b> <mark style="background:rgba(16,185,129,0.2);color:#fff;padding:2px 6px;border-radius:4px;">Enabled (60s)</mark>'
  }
};

function handleSimKey(e) {
  if (e.key === 'Enter') {
    sendSimMessage();
  }
}

function simulateCommand(cmd) {
  const input = document.getElementById('sim-input-field');
  if (input) {
    input.value = cmd;
    sendSimMessage();
  }
}

function sendSimMessage() {
  const input = document.getElementById('sim-input-field');
  const chat = document.getElementById('sim-chat');
  if (!input || !chat || !input.value.trim()) return;

  const userQuery = input.value.trim();
  input.value = '';

  // Render User Msg
  const userMsgHtml = `
    <div class="sim-msg">
      <div class="sim-avatar" style="background: linear-gradient(135deg, #7c3aed, #ec4899);">U</div>
      <div class="sim-msg-content">
        <div class="sim-msg-header">
          <span class="sim-author">You</span>
          <span class="sim-time">Just now</span>
        </div>
        <div class="sim-text">${escapeHtml(userQuery)}</div>
      </div>
    </div>
  `;
  chat.insertAdjacentHTML('beforeend', userMsgHtml);
  chat.scrollTop = chat.scrollHeight;

  // Typing indicator
  const typingId = 'typing-' + Date.now();
  const typingHtml = `
    <div class="sim-msg" id="${typingId}">
      <div class="sim-avatar" style="background: linear-gradient(135deg, var(--pink), var(--purple));">🌸</div>
      <div class="sim-msg-content">
        <div class="sim-msg-header">
          <span class="sim-author">Smart Bot</span>
          <span class="sim-bot-tag">BOT</span>
        </div>
        <div class="sim-text" style="color: #9ca3af; font-style: italic;">Smart Bot is thinking... 🌸</div>
      </div>
    </div>
  `;
  chat.insertAdjacentHTML('beforeend', typingHtml);
  chat.scrollTop = chat.scrollHeight;

  // Bot response resolution
  setTimeout(() => {
    const typingEl = document.getElementById(typingId);
    if (typingEl) typingEl.remove();

    let resp = SIM_RESPONSES['/setup'];
    const queryLower = userQuery.toLowerCase();

    if (queryLower.includes('health') || queryLower.includes('score')) {
      resp = SIM_RESPONSES['/health'];
    } else if (queryLower.includes('dna') || queryLower.includes('archetype')) {
      resp = SIM_RESPONSES['/dna'];
    } else if (queryLower.includes('slap') || queryLower.includes('bonk') || queryLower.includes('hug')) {
      resp = SIM_RESPONSES['slap'];
    } else if (queryLower.includes('lock') || queryLower.includes('ban') || queryLower.includes('mute')) {
      resp = SIM_RESPONSES['lock'];
    } else {
      resp = {
        text: `Received: "${escapeHtml(userQuery)}" — I have parsed your command and updated the server state! ✨`,
        embed: '<b>✨ Action Status:</b> Executed with 0.8s neural latency.<br/><b>Memory Synced:</b> SQLite Persistent Node updated.'
      };
    }

    const botMsgHtml = `
      <div class="sim-msg">
        <div class="sim-avatar" style="background: linear-gradient(135deg, var(--pink), var(--purple));">🌸</div>
        <div class="sim-msg-content">
          <div class="sim-msg-header">
            <span class="sim-author">Smart Bot</span>
            <span class="sim-bot-tag">BOT</span>
            <span class="sim-time">Just now</span>
          </div>
          <div class="sim-text">
            ${resp.text}
            ${resp.embed ? `<div class="sim-card-embed">${resp.embed}</div>` : ''}
          </div>
        </div>
      </div>
    `;
    chat.insertAdjacentHTML('beforeend', botMsgHtml);
    chat.scrollTop = chat.scrollHeight;
  }, 650);
}

function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

// 7. Toast Notification
function showToast(msg) {
  const toast = document.getElementById('toast');
  if (!toast) return;
  toast.textContent = msg;
  toast.classList.add('show');
  setTimeout(() => toast.classList.remove('show'), 3200);
}

// 8. Live Gateway Telemetry Pulse
async function fetchLiveTelemetry() {
  try {
    const res = await fetch('https://smart-bot-discord-engine.onrender.com/telemetry');
    const data = await res.json();
    if (data.discord_ping_ms) {
      const pingEl = document.getElementById('live-ping');
      if (pingEl) pingEl.textContent = data.discord_ping_ms + ' ms';
    }
  } catch (err) {
    // Silent fallback
  }
}
setInterval(fetchLiveTelemetry, 30000);
