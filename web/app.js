// ==============================================================================
// SMART BOT OS — TIER-1 WEB APPLICATION STATE ENGINE
// ==============================================================================

// State Management
let currentRole = 'visitor'; // visitor | member | admin | owner
let billingCycle = 'monthly'; // monthly | annual

// ------------------------------------------------------------------------------
// 1. NEURAL BACKGROUND PARTICLES CANVAS
// ------------------------------------------------------------------------------
(function initNeuralCanvas() {
  const canvas = document.getElementById('neural-canvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  let width, height, particles;

  function resize() {
    width = canvas.width = window.innerWidth;
    height = canvas.height = window.innerHeight;
    particles = [];
    const count = Math.floor((width * height) / 22000);
    for (let i = 0; i < count; i++) {
      particles.push({
        x: Math.random() * width,
        y: Math.random() * height,
        vx: (Math.random() - 0.5) * 0.4,
        vy: (Math.random() - 0.5) * 0.4,
        radius: Math.random() * 1.5 + 0.5,
        color: Math.random() > 0.5 ? '#5865F2' : '#00F0FF'
      });
    }
  }

  function render() {
    ctx.clearRect(0, 0, width, height);
    for (let i = 0; i < particles.length; i++) {
      const p = particles[i];
      p.x += p.vx;
      p.y += p.vy;
      if (p.x < 0 || p.x > width) p.vx *= -1;
      if (p.y < 0 || p.y > height) p.vy *= -1;

      ctx.beginPath();
      ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
      ctx.fillStyle = p.color;
      ctx.fill();

      for (let j = i + 1; j < particles.length; j++) {
        const p2 = particles[j];
        const dist = Math.hypot(p.x - p2.x, p.y - p2.y);
        if (dist < 90) {
          ctx.beginPath();
          ctx.moveTo(p.x, p.y);
          ctx.lineTo(p2.x, p2.y);
          ctx.strokeStyle = `rgba(88, 101, 242, ${0.15 * (1 - dist / 90)})`;
          ctx.lineWidth = 0.6;
          ctx.stroke();
        }
      }
    }
    requestAnimationFrame(render);
  }

  window.addEventListener('resize', resize);
  resize();
  render();
})();

// ------------------------------------------------------------------------------
// 2. AUTH MODAL & ROLE PORTAL ROUTING
// ------------------------------------------------------------------------------
function openAuthModal() {
  document.getElementById('auth-modal').classList.remove('hidden');
}

function closeAuthModal() {
  document.getElementById('auth-modal').classList.add('hidden');
}

function selectRole(role) {
  currentRole = role;
  closeAuthModal();

  // Hide all views
  document.getElementById('public-landing-view').classList.add('hidden');
  document.getElementById('member-portal-view').classList.add('hidden');
  document.getElementById('admin-portal-view').classList.add('hidden');
  document.getElementById('owner-portal-view').classList.add('hidden');

  const authLabel = document.getElementById('auth-label');
  const authIcon = document.getElementById('auth-icon');

  if (role === 'member') {
    document.getElementById('member-portal-view').classList.remove('hidden');
    authLabel.innerText = '👤 Member Hub';
    authIcon.className = 'fa-solid fa-user text-cyan';
  } else if (role === 'admin') {
    document.getElementById('admin-portal-view').classList.remove('hidden');
    authLabel.innerText = '🛡️ Admin Console';
    authIcon.className = 'fa-solid fa-shield-halved text-emerald-400';
  } else if (role === 'owner') {
    document.getElementById('owner-portal-view').classList.remove('hidden');
    authLabel.innerText = '👑 Master Panel';
    authIcon.className = 'fa-solid fa-crown text-amber-400';
  } else {
    document.getElementById('public-landing-view').classList.remove('hidden');
    authLabel.innerText = 'Login with Discord';
    authIcon.className = 'fa-brands fa-discord text-blurple';
  }

  window.scrollTo({ top: 0, behavior: 'smooth' });
}

function logoutRole() {
  selectRole('visitor');
}

// ------------------------------------------------------------------------------
// 3. INTERACTIVE SANDBOX SIMULATOR
// ------------------------------------------------------------------------------
const SIM_RESPONSES = {
  health: `
    <div class="discord-embed-card border-l-4 border-emerald-400 bg-surface/90 border border-white/[0.06] rounded-r-xl p-4 mt-2">
      <div class="flex items-center justify-between border-b border-white/[0.08] pb-2 mb-2">
        <span class="font-bold text-white text-sm">📈 Community Health Score — Sophie ♡'s Cave</span>
        <span class="text-emerald-400 font-mono font-bold text-base">88/100 (A)</span>
      </div>
      <div class="text-xs text-slate-300 space-y-1">
        <p>• <strong>Engagement:</strong> 18/25 (Healthy)</p>
        <p>• <strong>Staff Health:</strong> 18/20 (Fast Response)</p>
        <p>• <strong>Friction Radar:</strong> 20/20 (Zero drama)</p>
      </div>
      <div class="mt-2.5 pt-2 border-t border-white/[0.06] text-[10px] text-cyan font-mono">
        Smart Bot Community Intelligence • Sub-60ms Causal Verification
      </div>
    </div>
  `,
  dna: `
    <div class="discord-embed-card border-l-4 border-purple-500 bg-surface/90 border border-white/[0.06] rounded-r-xl p-4 mt-2">
      <div class="flex items-center justify-between border-b border-white/[0.08] pb-2 mb-2">
        <span class="font-bold text-white text-sm">🧬 Server DNA Profile — Sophie ♡'s Cave</span>
        <span class="text-purple-400 font-mono font-bold text-xs">85% Confidence</span>
      </div>
      <div class="text-xs text-slate-300 space-y-1">
        <p>• <strong>Archetype:</strong> General Community & Hangout</p>
        <p>• <strong>Communication Style:</strong> Casual & Friendly</p>
        <p>• <strong>Core Topics:</strong> Gaming, Music, Server Events</p>
      </div>
      <div class="mt-2.5 pt-2 border-t border-white/[0.06] text-[10px] text-purple-300 font-mono">
        Smart Bot Autonomous Core
      </div>
    </div>
  `,
  rule: `
    <p class="text-sm text-slate-200 mt-1">
      According to <strong>#announcements record (Decision ID #42)</strong>, the tournament date was moved to <em>Saturday at 8:00 PM UTC</em> to avoid conflict with the server game patch release! 🎮
    </p>
  `,
  poll: `
    <div class="discord-embed-card border-l-4 border-blurple bg-surface/90 border border-white/[0.06] rounded-r-xl p-4 mt-2">
      <span class="font-bold text-white text-sm block mb-2">📊 Community Vote: Which game for Friday Night?</span>
      <div class="space-y-1.5 text-xs">
        <div class="p-2 rounded bg-white/[0.04] flex justify-between"><span>1️⃣ Valorant Custom 5v5</span><span class="text-cyan font-bold font-mono">64% (32 votes)</span></div>
        <div class="p-2 rounded bg-white/[0.04] flex justify-between"><span>2️⃣ Among Us & Jackbox</span><span class="text-slate-400 font-mono">36% (18 votes)</span></div>
      </div>
      <div class="mt-2 pt-2 border-t border-white/[0.06] text-[10px] text-slate-500">
        Poll active • Closes in 24 hours
      </div>
    </div>
  `
};

function simulatePrompt(type) {
  const chatBox = document.getElementById('simulator-chat-box');
  const promptMap = {
    health: 'what is our community health score?',
    dna: 'inspect server dna and communication style',
    rule: 'why was the tournament date moved?',
    poll: 'native poll "Which game for Friday?" Valorant, Jackbox'
  };

  const userText = promptMap[type] || 'Hello Smart Bot!';
  
  // Add User Row
  const userHtml = `
    <div class="discord-msg-row">
      <div class="w-8 h-8 rounded-full bg-purple-600 flex items-center justify-center text-white font-bold text-xs shrink-0">
        You
      </div>
      <div>
        <div class="flex items-center gap-2">
          <span class="text-white font-semibold text-xs">You</span>
          <span class="text-[10px] text-slate-500">Just now</span>
        </div>
        <p class="text-slate-200 text-sm mt-0.5">@Smart bot ${userText}</p>
      </div>
    </div>
  `;
  chatBox.insertAdjacentHTML('beforeend', userHtml);

  // Add Bot Typing Row then replace
  const botHtml = `
    <div class="discord-msg-row">
      <img src="assets/avatar.jpg" alt="Smart Bot" class="w-8 h-8 rounded-full object-cover shrink-0" />
      <div>
        <div class="flex items-center gap-2">
          <span class="text-white font-bold text-xs">Smart bot</span>
          <span class="text-[9px] font-bold px-1 rounded bg-blurple text-white">APP</span>
          <span class="text-[10px] text-slate-500">Just now</span>
        </div>
        ${SIM_RESPONSES[type] || '<p class="text-sm text-slate-200 mt-1">I am processing your command with 100% causal verification! ⚡</p>'}
      </div>
    </div>
  `;

  setTimeout(() => {
    chatBox.insertAdjacentHTML('beforeend', botHtml);
    chatBox.scrollTop = chatBox.scrollHeight;
  }, 350);

  chatBox.scrollTop = chatBox.scrollHeight;
}

function handleSimulatorSubmit(e) {
  e.preventDefault();
  const input = document.getElementById('simulator-input');
  const val = input.value.trim();
  if (!val) return;

  const chatBox = document.getElementById('simulator-chat-box');
  const userHtml = `
    <div class="discord-msg-row">
      <div class="w-8 h-8 rounded-full bg-purple-600 flex items-center justify-center text-white font-bold text-xs shrink-0">
        You
      </div>
      <div>
        <div class="flex items-center gap-2">
          <span class="text-white font-semibold text-xs">You</span>
          <span class="text-[10px] text-slate-500">Just now</span>
        </div>
        <p class="text-slate-200 text-sm mt-0.5">${val}</p>
      </div>
    </div>
  `;
  chatBox.insertAdjacentHTML('beforeend', userHtml);
  input.value = '';

  setTimeout(() => {
    const replyHtml = `
      <div class="discord-msg-row">
        <img src="assets/avatar.jpg" alt="Smart Bot" class="w-8 h-8 rounded-full object-cover shrink-0" />
        <div>
          <div class="flex items-center gap-2">
            <span class="text-white font-bold text-xs">Smart bot</span>
            <span class="text-[9px] font-bold px-1 rounded bg-blurple text-white">APP</span>
            <span class="text-[10px] text-slate-500">Just now</span>
          </div>
          <p class="text-sm text-slate-200 mt-1">
            Understood! I verified your query against the server's Living Knowledge Graph. Everything is grounded with factual zero-hallucination accuracy. ⚡
          </p>
        </div>
      </div>
    `;
    chatBox.insertAdjacentHTML('beforeend', replyHtml);
    chatBox.scrollTop = chatBox.scrollHeight;
  }, 400);
}

function clearSimulatorChat() {
  const chatBox = document.getElementById('simulator-chat-box');
  chatBox.innerHTML = `
    <div class="discord-msg-row">
      <img src="assets/avatar.jpg" alt="Smart Bot" class="w-8 h-8 rounded-full object-cover shrink-0" />
      <div>
        <div class="flex items-center gap-2">
          <span class="text-white font-bold text-xs">Smart bot</span>
          <span class="text-[9px] font-bold px-1 rounded bg-blurple text-white">APP</span>
          <span class="text-[10px] text-slate-500">Just now</span>
        </div>
        <p class="text-sm text-slate-200 mt-1">
          Chat cleared. Click a quick prompt chip or type below to test! 🚀
        </p>
      </div>
    </div>
  `;
}

// ------------------------------------------------------------------------------
// 4. SEARCHABLE COMMANDS FILTER
// ------------------------------------------------------------------------------
function filterCommands(query) {
  const q = query.toLowerCase().trim();
  const cards = document.querySelectorAll('.command-card');
  cards.forEach(card => {
    const text = card.innerText.toLowerCase();
    if (!q || text.includes(q)) {
      card.style.display = 'block';
    } else {
      card.style.display = 'none';
    }
  });
}

// ------------------------------------------------------------------------------
// 5. PRICING BILLING CYCLE TOGGLE
// ------------------------------------------------------------------------------
function setBillingCycle(cycle) {
  billingCycle = cycle;
  const btnMonthly = document.getElementById('billing-monthly');
  const btnAnnual = document.getElementById('billing-annual');
  const priceStarter = document.getElementById('price-starter');
  const pricePro = document.getElementById('price-pro');

  if (cycle === 'annual') {
    btnAnnual.className = 'px-5 py-2 rounded-full text-xs font-bold bg-blurple text-white transition-all flex items-center gap-1.5';
    btnMonthly.className = 'px-5 py-2 rounded-full text-xs font-bold text-slate-400 hover:text-white transition-all';
    priceStarter.innerText = '$15';
    pricePro.innerText = '$39';
  } else {
    btnMonthly.className = 'px-5 py-2 rounded-full text-xs font-bold bg-blurple text-white transition-all';
    btnAnnual.className = 'px-5 py-2 rounded-full text-xs font-bold text-slate-400 hover:text-white transition-all flex items-center gap-1.5';
    priceStarter.innerText = '$19';
    pricePro.innerText = '$49';
  }
}
