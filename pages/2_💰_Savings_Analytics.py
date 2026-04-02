"""
Savings Analytics Dashboard – Sponsored AI
Shows a full breakdown of API cost savings driven by sponsored content.
"""

from collections import Counter
from datetime import datetime

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st

from cost_calculator import format_usd, GPT52_PRICING, REVENUE_PER_ORG_USD

st.set_page_config(
    page_title="Savings Analytics – Sponsored AI",
    page_icon="💰",
    layout="wide",
)

# ─── Custom CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

    .stat-card {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        border-radius: 14px;
        padding: 1.4rem 1.6rem;
        text-align: center;
        border: 1px solid #2a2a4a;
        margin-bottom: 1rem;
        box-shadow: 0 4px 20px rgba(0,0,0,0.4);
    }
    .stat-value { font-size: 2rem; font-weight: 700; margin: 0.2rem 0; }
    .stat-label { font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.08em; color: #666; }
    .stat-sub   { font-size: 0.78rem; color: #555; margin-top: 0.15rem; }

    .green { color: #2ECC71; }
    .blue  { color: #1E90FF; }
    .gray  { color: #888; }
    .gold  { color: #F4C430; }
    .red   { color: #E74C3C; }

    .section-header {
        font-size: 1.2rem;
        font-weight: 600;
        color: #ccc;
        margin: 1.8rem 0 0.8rem;
        border-left: 3px solid #1E90FF;
        padding-left: 0.75rem;
    }
    .empty-state {
        text-align: center;
        padding: 5rem 2rem;
        color: #555;
    }
    .empty-state .icon { font-size: 4rem; margin-bottom: 1rem; }
    .org-pill {
        display: inline-block;
        background: rgba(30,144,255,0.12);
        color: #5aabff;
        border-radius: 20px;
        padding: 2px 10px;
        margin: 2px;
        font-size: 0.78rem;
    }
    .pricing-note {
        background: #111827;
        border: 1px solid #1f2937;
        border-radius: 8px;
        padding: 0.6rem 1rem;
        font-size: 0.75rem;
        color: #6b7280;
        margin-bottom: 1.5rem;
    }
    .highlight-box {
        background: linear-gradient(135deg, #0d2818 0%, #0a1628 100%);
        border: 1px solid #1a4731;
        border-radius: 10px;
        padding: 1rem 1.4rem;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# ─── Page header ─────────────────────────────────────────────────────────────
st.title("💰 Savings Analytics")
st.markdown("*See exactly how Sponsored AI cuts your API costs through integrated sponsorships.*")

st.markdown(f"""
<div class="pricing-note">
  📋 &nbsp; Pricing model: <strong>{GPT52_PRICING['model']}</strong> &nbsp;·&nbsp;
  ${GPT52_PRICING['input_per_1m_tokens']:.2f}/1M input tokens &nbsp;·&nbsp;
  ${GPT52_PRICING['output_per_1m_tokens']:.2f}/1M output tokens &nbsp;·&nbsp;
  Sponsored revenue: <strong>${REVENUE_PER_ORG_USD}/org</strong> shown per response &nbsp;·&nbsp;
  Token counts: word × 1.35 approximation
</div>
""", unsafe_allow_html=True)

# ─── Guard: no data yet ──────────────────────────────────────────────────────
cost_history: list[dict] = st.session_state.get("cost_history", [])

if not cost_history:
    st.markdown("""
    <div class="empty-state">
        <div class="icon">📊</div>
        <h3 style="color:#888;">No session data yet</h3>
        <p style="max-width:420px; margin:0 auto; line-height:1.7;">
            Head over to the <strong>💬 Chat</strong> page, ask a few questions,
            then come back here to see your full savings breakdown — charts, tables,
            and cumulative timelines included.
        </p>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# ─── Aggregate totals ─────────────────────────────────────────────────────────
total_original   = sum(e["cost"]["original_cost_usd"] for e in cost_history)
total_savings    = sum(e["cost"]["savings_usd"]        for e in cost_history)
total_net        = sum(e["cost"]["your_cost_usd"]      for e in cost_history)
total_revenue    = sum(e["cost"]["revenue_earned_usd"] for e in cost_history)
total_tokens_in  = sum(e["cost"]["input_tokens"]       for e in cost_history)
total_tokens_out = sum(e["cost"]["output_tokens"]      for e in cost_history)
all_orgs         = [org for e in cost_history for org in e["cost"]["orgs_featured"]]
unique_orgs      = list(dict.fromkeys(all_orgs))
overall_pct      = round((total_savings / total_original * 100), 1) if total_original > 0 else 0.0
queries_with_savings = sum(1 for e in cost_history if e["cost"]["savings_usd"] > 0)

# ─── KPI cards ───────────────────────────────────────────────────────────────
st.markdown('<div class="section-header">📊 Session Summary</div>', unsafe_allow_html=True)

c1, c2, c3, c4, c5, c6 = st.columns(6)

with c1:
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-label">Total Queries</div>
        <div class="stat-value blue">{len(cost_history)}</div>
        <div class="stat-sub">{queries_with_savings} with savings</div>
    </div>""", unsafe_allow_html=True)

with c2:
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-label">Original Cost</div>
        <div class="stat-value gray">{format_usd(total_original)}</div>
        <div class="stat-sub">without sponsorship</div>
    </div>""", unsafe_allow_html=True)

with c3:
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-label">You Pay</div>
        <div class="stat-value blue">{format_usd(total_net)}</div>
        <div class="stat-sub">net cost after savings</div>
    </div>""", unsafe_allow_html=True)

with c4:
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-label">Total Saved</div>
        <div class="stat-value green">{format_usd(total_savings)}</div>
        <div class="stat-sub">{overall_pct}% cost reduction</div>
    </div>""", unsafe_allow_html=True)

with c5:
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-label">Revenue Earned</div>
        <div class="stat-value gold">{format_usd(total_revenue)}</div>
        <div class="stat-sub">from sponsors shown</div>
    </div>""", unsafe_allow_html=True)

with c6:
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-label">Sponsors Shown</div>
        <div class="stat-value gold">{len(all_orgs)}</div>
        <div class="stat-sub">{len(unique_orgs)} unique sponsors</div>
    </div>""", unsafe_allow_html=True)

st.markdown("---")

# ─── Row 1: Pie chart + Per-query bar chart ───────────────────────────────────
col_pie, col_bar = st.columns([1, 1], gap="large")

with col_pie:
    st.markdown('<div class="section-header">🥧 Cost Breakdown</div>', unsafe_allow_html=True)

    # Pie shows: what you actually pay + what sponsors covered
    net_display  = max(round(total_net,      6), 0)
    save_display = max(round(total_savings,  6), 0)

    if net_display + save_display > 0:
        fig_pie = go.Figure(data=[go.Pie(
            labels=["You Pay (Net)", "Sponsor Offset"],
            values=[net_display, save_display],
            hole=0.52,
            marker=dict(
                colors=["#1E90FF", "#2ECC71"],
                line=dict(color="#0e1117", width=2),
            ),
            textinfo="label+percent",
            textfont=dict(size=12, color="white"),
            hovertemplate=(
                "<b>%{label}</b><br>"
                "Amount: $%{value:.6f}<br>"
                "Share of original cost: %{percent}<extra></extra>"
            ),
        )])
        fig_pie.add_annotation(
            text=f"<b>{overall_pct}%</b><br><span style='font-size:11px'>saved</span>",
            x=0.5, y=0.5,
            font=dict(size=18, color="#2ECC71"),
            showarrow=False,
        )
        fig_pie.update_layout(
            paper_bgcolor="#0e1117",
            plot_bgcolor="#0e1117",
            font=dict(color="white", family="Inter"),
            legend=dict(bgcolor="#1a1a2e", bordercolor="#2a2a4a", borderwidth=1, font=dict(color="#ccc")),
            margin=dict(t=10, b=10, l=10, r=10),
            height=320,
        )
        st.plotly_chart(fig_pie, use_container_width=True)
    else:
        st.info("All queries had zero measurable cost — nothing to chart yet.")

with col_bar:
    st.markdown('<div class="section-header">📈 Cost Per Query</div>', unsafe_allow_html=True)

    q_labels    = [f"Q{i+1}" for i in range(len(cost_history))]
    orig_vals   = [e["cost"]["original_cost_usd"] for e in cost_history]
    net_vals    = [e["cost"]["your_cost_usd"]      for e in cost_history]
    save_vals   = [e["cost"]["savings_usd"]        for e in cost_history]
    hover_texts = [
        f"<b>{e.get('prompt_snippet', f'Query {i+1}')}</b>"
        for i, e in enumerate(cost_history)
    ]

    fig_bar = go.Figure()
    fig_bar.add_trace(go.Bar(
        name="Original Cost", x=q_labels, y=orig_vals,
        marker_color="#444", opacity=0.75,
        hovertemplate="%{customdata}<br>Original: $%{y:.6f}<extra></extra>",
        customdata=hover_texts,
    ))
    fig_bar.add_trace(go.Bar(
        name="You Pay", x=q_labels, y=net_vals,
        marker_color="#1E90FF",
        hovertemplate="%{customdata}<br>You Pay: $%{y:.6f}<extra></extra>",
        customdata=hover_texts,
    ))
    fig_bar.add_trace(go.Bar(
        name="Savings", x=q_labels, y=save_vals,
        marker_color="#2ECC71",
        hovertemplate="%{customdata}<br>Savings: $%{y:.6f}<extra></extra>",
        customdata=hover_texts,
    ))
    fig_bar.update_layout(
        barmode="group",
        paper_bgcolor="#0e1117",
        plot_bgcolor="#111827",
        font=dict(color="#aaa", family="Inter"),
        xaxis=dict(title="Query #", gridcolor="#1f2937"),
        yaxis=dict(title="Cost (USD)", gridcolor="#1f2937", tickformat="$.6f"),
        legend=dict(bgcolor="#1a1a2e", bordercolor="#2a2a4a", borderwidth=1, font=dict(color="#ccc")),
        margin=dict(t=10, b=40, l=10, r=10),
        height=320,
    )
    st.plotly_chart(fig_bar, use_container_width=True)

# ─── Row 2: Cumulative savings timeline + Savings-rate per query ──────────────
if len(cost_history) >= 2:
    col_cum, col_rate = st.columns([1, 1], gap="large")

    with col_cum:
        st.markdown('<div class="section-header">📉 Cumulative Savings Over Time</div>', unsafe_allow_html=True)

        cum_orig  = []
        cum_net   = []
        cum_saved = []
        run_orig = run_net = run_saved = 0.0

        for e in cost_history:
            run_orig  += e["cost"]["original_cost_usd"]
            run_net   += e["cost"]["your_cost_usd"]
            run_saved += e["cost"]["savings_usd"]
            cum_orig.append(run_orig)
            cum_net.append(run_net)
            cum_saved.append(run_saved)

        x_axis = list(range(1, len(cost_history) + 1))

        fig_cum = go.Figure()
        fig_cum.add_trace(go.Scatter(
            x=x_axis, y=cum_orig,
            name="Cumulative Original",
            line=dict(color="#555", width=2, dash="dot"),
            mode="lines",
        ))
        fig_cum.add_trace(go.Scatter(
            x=x_axis, y=cum_net,
            name="Cumulative You Pay",
            line=dict(color="#1E90FF", width=2),
            mode="lines+markers",
            marker=dict(size=6),
        ))
        fig_cum.add_trace(go.Scatter(
            x=x_axis, y=cum_saved,
            name="Cumulative Saved",
            line=dict(color="#2ECC71", width=2),
            fill="tozeroy",
            fillcolor="rgba(46,204,113,0.08)",
            mode="lines+markers",
            marker=dict(size=6),
        ))
        fig_cum.update_layout(
            paper_bgcolor="#0e1117",
            plot_bgcolor="#111827",
            font=dict(color="#aaa", family="Inter"),
            xaxis=dict(title="Query #", gridcolor="#1f2937", dtick=1),
            yaxis=dict(title="Cumulative USD", gridcolor="#1f2937", tickformat="$.6f"),
            legend=dict(bgcolor="#1a1a2e", bordercolor="#2a2a4a", borderwidth=1, font=dict(color="#ccc")),
            margin=dict(t=10, b=40, l=10, r=10),
            height=300,
        )
        st.plotly_chart(fig_cum, use_container_width=True)

    with col_rate:
        st.markdown('<div class="section-header">🎯 Savings Rate Per Query (%)</div>', unsafe_allow_html=True)

        rates = [e["cost"]["savings_pct"] for e in cost_history]
        avg_rate = round(sum(rates) / len(rates), 1) if rates else 0.0

        colors = ["#2ECC71" if r >= 50 else "#E67E22" if r > 0 else "#E74C3C" for r in rates]

        fig_rate = go.Figure(go.Bar(
            x=q_labels, y=rates,
            marker_color=colors,
            text=[f"{r}%" for r in rates],
            textposition="outside",
            textfont=dict(color="white", size=11),
            hovertemplate="<b>%{x}</b><br>Savings rate: %{y:.1f}%<extra></extra>",
        ))
        fig_rate.add_hline(
            y=avg_rate,
            line_dash="dot",
            line_color="#F4C430",
            annotation_text=f"avg {avg_rate}%",
            annotation_font_color="#F4C430",
        )
        fig_rate.update_layout(
            paper_bgcolor="#0e1117",
            plot_bgcolor="#111827",
            font=dict(color="#aaa", family="Inter"),
            xaxis=dict(title="Query #", gridcolor="#1f2937"),
            yaxis=dict(title="Savings %", gridcolor="#1f2937", range=[0, max(max(rates) * 1.2, 10)]),
            margin=dict(t=10, b=40, l=10, r=30),
            height=300,
        )
        st.plotly_chart(fig_rate, use_container_width=True)

# ─── Sponsor frequency chart ──────────────────────────────────────────────────
if all_orgs:
    st.markdown('<div class="section-header">🏢 Most-Featured Sponsors This Session</div>', unsafe_allow_html=True)

    org_counts = Counter(all_orgs)
    org_df = pd.DataFrame(org_counts.items(), columns=["Company", "Times Featured"]).sort_values(
        "Times Featured", ascending=True
    )

    fig_orgs = px.bar(
        org_df,
        x="Times Featured",
        y="Company",
        orientation="h",
        color="Times Featured",
        color_continuous_scale=["#1a2a4a", "#1E90FF"],
        text="Times Featured",
    )
    fig_orgs.update_traces(textposition="outside", textfont_color="white")
    fig_orgs.update_layout(
        paper_bgcolor="#0e1117",
        plot_bgcolor="#111827",
        font=dict(color="#aaa", family="Inter"),
        xaxis=dict(title="Times featured in responses", gridcolor="#1f2937"),
        yaxis=dict(gridcolor="#1f2937"),
        coloraxis_showscale=False,
        margin=dict(t=10, b=20, l=10, r=60),
        height=max(220, len(org_df) * 44),
    )
    st.plotly_chart(fig_orgs, use_container_width=True)

# ─── Per-query detail table ────────────────────────────────────────────────────
st.markdown('<div class="section-header">📋 Per-Query Breakdown</div>', unsafe_allow_html=True)

rows = []
for i, entry in enumerate(cost_history):
    c = entry["cost"]
    ts = entry.get("timestamp", "")
    # Format timestamp for display if present
    if ts:
        try:
            ts_display = datetime.fromisoformat(ts).strftime("%H:%M:%S")
        except Exception:
            ts_display = ts
    else:
        ts_display = f"Q{i+1}"

    rows.append({
        "#":             i + 1,
        "Time":          ts_display,
        "Query":         entry.get("prompt_snippet", f"Query {i+1}"),
        "In Tokens":     c["input_tokens"],
        "Out Tokens":    c["output_tokens"],
        "Original Cost": format_usd(c["original_cost_usd"]),
        "Revenue":       format_usd(c["revenue_earned_usd"]),
        "Savings":       format_usd(c["savings_usd"]),
        "You Pay":       format_usd(c["your_cost_usd"]),
        "Saved %":       f"{c['savings_pct']}%",
        "Sponsors":      ", ".join(c["orgs_featured"]) if c["orgs_featured"] else "—",
    })

df = pd.DataFrame(rows)
st.dataframe(
    df,
    use_container_width=True,
    hide_index=True,
    column_config={
        "#":             st.column_config.NumberColumn(width="small"),
        "Time":          st.column_config.TextColumn(width="small"),
        "Query":         st.column_config.TextColumn(width="large"),
        "In Tokens":     st.column_config.NumberColumn(width="small"),
        "Out Tokens":    st.column_config.NumberColumn(width="small"),
        "Saved %":       st.column_config.TextColumn(width="small"),
        "Sponsors":      st.column_config.TextColumn(width="medium"),
    },
)

# ─── Footer ───────────────────────────────────────────────────────────────────
st.markdown("---")
st.caption(
    f"💡 Savings are calculated by offsetting the {GPT52_PRICING['model']} API cost with "
    f"${REVENUE_PER_ORG_USD} revenue per sponsored organisation shown in each response. "
    "Sponsors are determined by which ads the RAG retrieval pipeline selected for each query. "
    "Token counts use a word × 1.35 approximation."
)
