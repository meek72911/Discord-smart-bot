export default async function handler(req, res) {
  const targetUrl = 'https://smart-bot-discord-engine.onrender.com';
  const startTime = Date.now();

  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 25000);

    const response = await fetch(targetUrl, {
      method: 'GET',
      headers: {
        'User-Agent': 'SmartBot-KeepAlive-Sentinel/2.0 (Vercel-Cron)'
      },
      signal: controller.signal
    });

    clearTimeout(timeoutId);
    const latency = Date.now() - startTime;
    let payload = null;
    try {
      payload = await response.json();
    } catch {
      payload = { status: 'online' };
    }

    return res.status(200).json({
      status: 'operational',
      gateway: 'Render Cloud (Oregon)',
      http_code: response.status,
      latency_ms: latency,
      bot_data: payload,
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    const latency = Date.now() - startTime;
    return res.status(200).json({
      status: 'waking_up',
      gateway: 'Render Cloud (Oregon)',
      note: 'Render container cold-start initiated',
      error: error.message || String(error),
      latency_ms: latency,
      timestamp: new Date().toISOString()
    });
  }
}
