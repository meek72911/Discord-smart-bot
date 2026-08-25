export default async function handler(req, res) {
  const targetUrl = 'https://smart-bot-discord-engine.onrender.com';
  const startTime = Date.now();

  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  // 1. Ping Render
  let renderResult = { status: 'pending' };
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 20000);
    const response = await fetch(targetUrl, {
      headers: { 'User-Agent': 'SmartBot-Sentinel/2.0' },
      signal: controller.signal
    });
    clearTimeout(timeoutId);
    renderResult = { status: 'online', http_code: response.status };
  } catch (err) {
    renderResult = { status: 'waking_up', error: String(err) };
  }

  // 2. Ping Supabase (Resets 7-day inactivity pause timer)
  let supabaseResult = { status: 'pending' };
  try {
    const response = await fetch('https://bmofhaqqusvwisjbccqn.supabase.co/rest/v1/', {
      headers: {
        'User-Agent': 'SmartBot-Sentinel/2.0'
      }
    });
    supabaseResult = { status: 'active_healthy', http_code: response.status };
  } catch (err) {
    supabaseResult = { status: 'pulsed', note: 'Pulse sent to Supabase' };
  }

  const latency = Date.now() - startTime;
  return res.status(200).json({
    sentinel: '24/7 Cloud Guardian',
    render: renderResult,
    supabase: supabaseResult,
    latency_ms: latency,
    timestamp: new Date().toISOString()
  });
}
