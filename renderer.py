"""
renderer.py — HTML dashboard renderer

Produces a self-contained HTML file using Jinja2 templating.
No JS dependencies — pure HTML/CSS. Opens in any browser with no server.

Output shape justification: HTML was chosen over a console summary or JSON
because it is richer than text, requires no server or build step to open,
and is easy to share with a non-technical support manager.
"""

import json
from datetime import datetime
from jinja2 import Template


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Support Triage Dashboard</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
         background: #f5f6fa; color: #1a1a2e; padding: 24px; }
  h1 { font-size: 1.6rem; font-weight: 700; margin-bottom: 4px; }
  .subtitle { color: #666; font-size: 0.9rem; margin-bottom: 24px; }
  .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 16px; margin-bottom: 24px; }
  .card { background: white; border-radius: 10px; padding: 20px; box-shadow: 0 1px 4px rgba(0,0,0,.08); }
  .card h2 { font-size: 0.8rem; text-transform: uppercase; letter-spacing: .06em; color: #888; margin-bottom: 12px; }
  .stat-row { display: flex; justify-content: space-between; align-items: center; padding: 6px 0; border-bottom: 1px solid #f0f0f0; font-size: 0.9rem; }
  .stat-row:last-child { border-bottom: none; }
  .badge { display: inline-block; padding: 2px 8px; border-radius: 20px; font-size: 0.75rem; font-weight: 600; }
  .badge-Critical { background: #fee2e2; color: #b91c1c; }
  .badge-High     { background: #ffedd5; color: #c2410c; }
  .badge-Medium   { background: #fef9c3; color: #854d0e; }
  .badge-Low      { background: #dcfce7; color: #166534; }
  .badge-Open     { background: #dbeafe; color: #1e40af; }
  .badge-Escalated{ background: #fee2e2; color: #b91c1c; }
  .badge-Resolved { background: #dcfce7; color: #166534; }
  .kpi-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 24px; }
  .kpi { background: white; border-radius: 10px; padding: 20px; text-align: center; box-shadow: 0 1px 4px rgba(0,0,0,.08); }
  .kpi .val { font-size: 2rem; font-weight: 700; }
  .kpi .lbl { font-size: 0.75rem; color: #888; margin-top: 4px; text-transform: uppercase; }
  .kpi.warn .val { color: #c2410c; }
  .kpi.ok   .val { color: #166534; }
  table { width: 100%; border-collapse: collapse; font-size: 0.82rem; }
  th { background: #f8f9fb; text-align: left; padding: 8px 10px; font-weight: 600; color: #555; font-size: 0.78rem; text-transform: uppercase; }
  td { padding: 8px 10px; border-bottom: 1px solid #f0f0f0; vertical-align: top; }
  tr:last-child td { border-bottom: none; }
  tr.recurrence td { background: #fffbeb; }
  .prior-list { font-size: 0.75rem; color: #888; }
  .full-width { grid-column: 1 / -1; }
  .risk-flag { color: #c2410c; font-weight: 600; }
  .bar-wrap { background: #f0f0f0; border-radius: 4px; height: 8px; flex: 1; margin-left: 10px; overflow: hidden; }
  .bar-fill { height: 100%; border-radius: 4px; background: #6366f1; }
  .stat-bar { display: flex; align-items: center; padding: 7px 0; border-bottom: 1px solid #f0f0f0; font-size: 0.88rem; }
  .stat-bar:last-child { border-bottom: none; }
  .stat-label { width: 140px; flex-shrink: 0; }
  .stat-val { width: 36px; text-align: right; font-weight: 600; color: #333; margin-left: 8px; }
</style>
</head>
<body>
<h1>Support Triage Dashboard</h1>
<p class="subtitle">Generated {{ generated_at }} · {{ dash.total_tickets }} tickets analysed</p>

<div class="kpi-grid">
  <div class="kpi warn">
    <div class="val">{{ dash.open_backlog.total }}</div>
    <div class="lbl">Open / Escalated</div>
  </div>
  <div class="kpi warn">
    <div class="val">{{ dash.open_backlog.escalated }}</div>
    <div class="lbl">Escalated</div>
  </div>
  <div class="kpi warn">
    <div class="val">{{ dash.missing_priority_pct }}%</div>
    <div class="lbl">Missing Priority</div>
  </div>
  <div class="kpi {{ 'ok' if dash.satisfaction.overall_avg and dash.satisfaction.overall_avg >= 3.5 else 'warn' }}">
    <div class="val">{{ dash.satisfaction.overall_avg or '-' }}</div>
    <div class="lbl">Avg Satisfaction</div>
  </div>
</div>

<div class="grid">

  <div class="card">
    <h2>Volume by Category</h2>
    {% set max_vol = dash.volume_by_category.values() | max %}
    {% for cat, cnt in dash.volume_by_category.items() | sort(attribute=1, reverse=True) %}
    <div class="stat-bar">
      <div class="stat-label">{{ cat }}</div>
      <div class="bar-wrap"><div class="bar-fill" style="width:{{ (cnt / max_vol * 100)|int }}%"></div></div>
      <div class="stat-val">{{ cnt }}</div>
    </div>
    {% endfor %}
  </div>

  <div class="card">
    <h2>Priority Distribution (AI-Suggested)</h2>
    {% for p in ['Critical','High','Medium','Low'] %}
    {% set cnt = dash.priority_distribution.get(p, 0) %}
    <div class="stat-row">
      <span><span class="badge badge-{{ p }}">{{ p }}</span></span>
      <span>{{ cnt }}</span>
    </div>
    {% endfor %}
  </div>

  <div class="card">
    <h2>Satisfaction by Category</h2>
    {% for cat, score in dash.satisfaction.by_category.items() | sort(attribute=1) %}
    <div class="stat-row">
      <span>{{ cat }}</span>
      <span style="color: {{ '#b91c1c' if score < 3 else ('#854d0e' if score < 4 else '#166534') }}; font-weight:600">{{ score }} / 5</span>
    </div>
    {% endfor %}
  </div>

  <div class="card">
    <h2>Avg Resolution Time (hrs)</h2>
    {% for cat, hrs in dash.avg_resolution_time_by_category.items() | sort(attribute=1, reverse=True) %}
    <div class="stat-row"><span>{{ cat }}</span><span>{{ hrs }}h</span></div>
    {% endfor %}
  </div>

  <div class="card">
    <h2>Recurring Customer Hotspots</h2>
    {% for cust, cnt in dash.recurring_customer_hotspots.items() %}
    <div class="stat-row">
      <span>{{ cust }}</span>
      <span class="{{ 'risk-flag' if cnt >= 4 else '' }}">{{ cnt }} tickets</span>
    </div>
    {% endfor %}
  </div>

  <div class="card">
    <h2>Customers At Risk (3+ tickets)</h2>
    {% for c in dash.customers_at_risk %}
    <div class="stat-row">
      <span>{{ c.customer_id }}<br><small class="prior-list">{{ c.ticket_count }} tickets · sat {{ c.avg_satisfaction or '-' }}/5</small></span>
      <span>
        {% if c.open_tickets %}<span class="badge badge-Open">{{ c.open_tickets | length }} open</span>{% endif %}
      </span>
    </div>
    {% endfor %}
  </div>

</div>

<div class="card full-width">
  <h2>Per-Ticket Triage Results</h2>
  <table>
    <thead>
      <tr>
        <th>Ticket</th>
        <th>Date</th>
        <th>Customer</th>
        <th>Priority</th>
        <th>Category / Sub</th>
        <th>Status</th>
        <th>Recurring</th>
        <th>Explanation</th>
      </tr>
    </thead>
    <tbody>
    {% for r in rows %}
    <tr class="{{ 'recurrence' if r.recurrence_flag else '' }}">
      <td><strong>{{ r.ticket_id }}</strong></td>
      <td>{{ r.date_submitted }}</td>
      <td>{{ r.customer_id }}</td>
      <td><span class="badge badge-{{ r.suggested_priority }}">{{ r.suggested_priority }}</span></td>
      <td>{{ r.suggested_category }}<br><small class="prior-list">{{ r.suggested_subcategory }}</small></td>
      <td><span class="badge badge-{{ r.status }}">{{ r.status }}</span></td>
      <td>
        {% if r.recurrence_flag %}
          Prior: <span class="prior-list">{{ r.prior_tickets | join(', ') }}</span>
        {% else %}-{% endif %}
      </td>
      <td style="max-width:320px">{{ r.explanation }}</td>
    </tr>
    {% endfor %}
    </tbody>
  </table>
</div>

</body>
</html>"""


def render_html(rows: list[dict], dashboard: dict, output_path: str) -> None:
    template = Template(HTML_TEMPLATE)
    html = template.render(
        rows=rows,
        dash=dashboard,
        generated_at=datetime.now().strftime("%Y-%m-%d %H:%M"),
    )
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
