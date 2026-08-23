"""
GreenGrid Interactive Dashboard HTML Template.

Provides an enterprise-grade dark-themed web console for monitoring
regional data center carbon intensity and executing carbon-optimal workload routing.
"""

DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GreenGrid | Carbon-Aware Infrastructure Console</title>
    <style>
        :root {
            --bg-primary: #0a0e17;
            --bg-secondary: #131b2e;
            --bg-card: #1c2640;
            --border-color: #2a3859;
            --text-primary: #f0f4fc;
            --text-secondary: #94a3b8;
            --accent-green: #10b981;
            --accent-blue: #3b82f6;
            --accent-amber: #f59e0b;
            --accent-red: #ef4444;
            --font-mono: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
        body { background: var(--bg-primary); color: var(--text-primary); padding: 24px; min-height: 100vh; }
        .container { max-width: 1200px; margin: 0 auto; }
        header { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid var(--border-color); padding-bottom: 16px; margin-bottom: 24px; }
        .logo { font-size: 20px; font-weight: 700; letter-spacing: -0.5px; color: var(--text-primary); display: flex; align-items: center; gap: 8px; }
        .badge { background: rgba(16, 185, 129, 0.15); color: var(--accent-green); padding: 4px 10px; border-radius: 9999px; font-size: 12px; font-weight: 600; border: 1px solid rgba(16, 185, 129, 0.3); }
        .grid-cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 16px; margin-bottom: 28px; }
        .card { background: var(--bg-card); border: 1px solid var(--border-color); border-radius: 8px; padding: 18px; }
        .card-title { font-size: 14px; color: var(--text-secondary); text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 8px; }
        .card-metric { font-size: 26px; font-weight: 700; font-family: var(--font-mono); color: var(--text-primary); margin-bottom: 6px; }
        .card-sub { font-size: 12px; color: var(--text-secondary); }
        .section-title { font-size: 16px; font-weight: 600; margin-bottom: 14px; border-left: 3px solid var(--accent-green); padding-left: 10px; }
        .main-layout { display: grid; grid-template-columns: 1fr 1fr; gap: 24px; }
        @media (max-width: 860px) { .main-layout { grid-template-columns: 1fr; } }
        .form-group { margin-bottom: 14px; }
        label { display: block; font-size: 13px; color: var(--text-secondary); margin-bottom: 6px; }
        input, select { width: 100%; background: var(--bg-secondary); border: 1px solid var(--border-color); color: var(--text-primary); padding: 10px 12px; border-radius: 6px; font-size: 14px; outline: none; }
        input:focus, select:focus { border-color: var(--accent-blue); }
        button { width: 100%; background: #059669; color: white; border: none; padding: 12px; border-radius: 6px; font-size: 14px; font-weight: 600; cursor: pointer; transition: background 0.2s; }
        button:hover { background: #10b981; }
        .console-box { background: var(--bg-secondary); border: 1px solid var(--border-color); border-radius: 6px; padding: 16px; font-family: var(--font-mono); font-size: 13px; min-height: 220px; line-height: 1.6; white-space: pre-wrap; overflow-x: auto; color: #cbd5e1; }
        .highlight-green { color: var(--accent-green); font-weight: bold; }
        .highlight-blue { color: var(--accent-blue); }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div class="logo">
                <span>GreenGrid Infrastructure Console</span>
                <span class="badge">PROD-SIMULATION v0.2.0</span>
            </div>
            <div>
                <a href="/docs" style="color: var(--accent-blue); font-size: 13px; text-decoration: none; margin-right: 16px;">API Docs</a>
                <a href="/web" style="color: var(--text-secondary); font-size: 13px; text-decoration: none;">OpenEnv Client</a>
            </div>
        </header>

        <div class="section-title">Live Regional Data Center Telemetry</div>
        <div class="grid-cards" id="datacenter-cards">
            <div class="card"><div class="card-title">Oregon (US-West)</div><div class="card-metric">124.2 <span style="font-size: 14px;">gCO2/kWh</span></div><div class="card-sub">Renewable: Hydro | PUE: 1.12</div></div>
            <div class="card"><div class="card-title">Frankfurt (EU-West)</div><div class="card-metric">231.8 <span style="font-size: 14px;">gCO2/kWh</span></div><div class="card-sub">Renewable: Wind/Solar | PUE: 1.15</div></div>
            <div class="card"><div class="card-title">Virginia (US-East)</div><div class="card-metric">384.5 <span style="font-size: 14px;">gCO2/kWh</span></div><div class="card-sub">Renewable: Mixed Nuclear | PUE: 1.18</div></div>
            <div class="card"><div class="card-title">Mumbai (IN-West)</div><div class="card-metric">442.0 <span style="font-size: 14px;">gCO2/kWh</span></div><div class="card-sub">Renewable: Solar Thermal | PUE: 1.25</div></div>
            <div class="card"><div class="card-title">Singapore (AP-South)</div><div class="card-metric">458.1 <span style="font-size: 14px;">gCO2/kWh</span></div><div class="card-sub">Renewable: Gas Cogen | PUE: 1.22</div></div>
        </div>

        <div class="main-layout">
            <div class="card">
                <div class="section-title" style="margin-top: 0;">Dispatch Workload</div>
                <form id="dispatch-form">
                    <div class="form-group">
                        <label for="job_id">Job Identifier</label>
                        <input type="text" id="job_id" value="train-finetune-llama3" required>
                    </div>
                    <div class="form-group">
                        <label for="compute_units">Normalized Compute Units (GPU-Hours)</label>
                        <input type="number" id="compute_units" value="16" min="1" max="1000" required>
                    </div>
                    <div class="form-group">
                        <label for="deadline">SLA Deadline (Hours)</label>
                        <input type="number" id="deadline" value="4" min="1" max="72" required>
                    </div>
                    <div class="form-group">
                        <label for="priority">Priority Tier</label>
                        <select id="priority">
                            <option value="low">Low Priority (Batch/Background)</option>
                            <option value="medium" selected>Medium Priority (Standard SLA)</option>
                            <option value="high">High Priority (Urgent)</option>
                        </select>
                    </div>
                    <button type="submit" id="submit-btn">Calculate Carbon-Optimal Routing</button>
                </form>
            </div>

            <div class="card">
                <div class="section-title" style="margin-top: 0;">Routing Decision Telemetry</div>
                <div class="console-box" id="console-output">Ready. Submit a workload directive to compute optimal placement...</div>
            </div>
        </div>
    </div>

    <script>
        async function updateTelemetry() {
            try {
                const res = await fetch('/api/v1/grid-telemetry');
                if (res.ok) {
                    const data = await res.json();
                    const container = document.getElementById('datacenter-cards');
                    container.innerHTML = '';
                    data.forEach(node => {
                        const card = document.createElement('div');
                        card.className = 'card';
                        card.innerHTML = `
                            <div class="card-title">${node.name} (${node.region_id})</div>
                            <div class="card-metric">${node.carbon_intensity.toFixed(1)} <span style="font-size: 14px;">gCO2/kWh</span></div>
                            <div class="card-sub">Renewable: ${node.renewable_primary} | $${node.cost_per_kwh_usd.toFixed(3)}/kWh</div>
                        `;
                        container.appendChild(card);
                    });
                }
            } catch (err) {
                console.error("Telemetry update failed", err);
            }
        }

        document.getElementById('dispatch-form').addEventListener('submit', async (e) => {
            e.preventDefault();
            const btn = document.getElementById('submit-btn');
            btn.disabled = true;
            btn.innerText = "Evaluating Grid Telemetry...";

            const payload = {
                job_id: document.getElementById('job_id').value,
                compute_units: parseFloat(document.getElementById('compute_units').value),
                deadline_hours: parseFloat(document.getElementById('deadline').value),
                priority: document.getElementById('priority').value,
                hour_of_day: 14.0
            };

            try {
                const res = await fetch('/api/v1/dispatch', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                const result = await res.json();
                const output = document.getElementById('console-output');
                output.innerHTML = `[OPTIMAL_ROUTE_RESOLVED]
Target Data Center     : <span class="highlight-green">${result.optimal_region} (${result.optimal_region_id})</span>
Grid Emission Rate     : ${result.instantaneous_carbon_g_kwh} gCO2/kWh
Total Carbon Emissions : <span class="highlight-blue">${result.estimated_emissions_kg_co2} kg CO2e</span>
Estimated Operating Cost: $${result.estimated_cost_usd}
Carbon Savings         : <span class="highlight-green">${result.carbon_savings_percent}% reduction</span> vs ${result.worst_case_region}
Routing Status         : ${result.dispatch_status}
Timestamp              : ${new Date().toISOString()}`;
            } catch (err) {
                document.getElementById('console-output').innerText = "[ERROR] Routing computation failed: " + err.message;
            } finally {
                btn.disabled = false;
                btn.innerText = "Calculate Carbon-Optimal Routing";
            }
        });

        // Initialize telemetry on load
        updateTelemetry();
        setInterval(updateTelemetry, 15000);
    </script>
</body>
</html>
"""
