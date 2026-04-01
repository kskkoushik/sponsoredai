"""
Savings Analytics Page - See how much you've saved with Sponsored AI.
Shows a pie chart and per-query breakdown of cost vs savings.
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from cost_calculator import format_usd, GPT52_PRICING, REVENUE_PER_ORG_USD

st.set_page_config(
    page_title="Savings Analytics - Sponsored AI",
    page_icon="💰",
    layout="wide"
)

# ─── Custom CSS ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    .stat-card {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        border-radius: 14px;
        padding: 1.4rem 1.6rem;
        text-align: center;
        border: 1px solid #2a2a4a;
        margin-bottom: 1rem;
        box-shadow: 0 4px 20px rgba(0,0,0,0.4);
    }
    .stat-value {
        font-size: 2rem;
        font-weight: 700;
        margin: 0.2rem 0;
    }
    .stat-label {
        font-size: 0.78rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: #666;
    }
    .stat-sub {
        font-size: 0.78rem;
        color: #555;
        margin-top: 0.15rem;
    }
    .green { color: #2ECC71; }
    .blue  { color: #1E90FF; }
    .gray  { color: #888; }
    .gold  { color: #F4C430; }

    .section-header {
        font-size: 1.25rem;
        font-weight: 600;
        color: #ccc;
        margin: 1.5rem 0 0.75rem;
        border-left: 3px solid #1E90FF;
        padding-left: 0.75rem;
    }
    .empty-state {
        text-align: center;
        padding: 4rem 2rem;
        color: #555;
    }
    .empty-state .icon {
        font-size: 4rem;
        margin-bottom: 1rem;
    }
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
</style>
""", unsafe_allow_html=True)

# ─── Page header ─────────────────────────────────────────────────────────────
st.title("💰 Savings Analytics")
st.markdown("*See how Sponsored AI reduces your API costs through integrated sponsorships*")

# Pricing note
st.markdown(f"""
<div class="pricing-note">
  📋 &nbsp; Pricing model: <strong>{GPT52_PRICING['model']}</strong> &nbsp;·&nbsp;
  ${GPT52_PRICING['input_per_1m_tokens']:.2f}/1M input tokens &nbsp;·&nbsp;
  ${GPT52_PRICING['output_per_1m_tokens']:.2f}/1M output tokens &nbsp;·&nbsp;
  Revenue: <strong>${REVENUE_PER_ORG_USD}/org</strong> shown per response
</div>
""", unsafe_allow_html=True)

# ─── Guard: no data yet ──────────────────────────────────────────────────────
cost_history = st.session_state.get("cost_history", [])

if not cost_history:
    st.markdown("""
    <div class="empty-state">
        <div class="icon">📊</div>
        <h3 style="color:#888;">No data yet</h3>
        <p>Head over to the <strong>Chat</strong> page, ask a few questions,<br>
        then come back here to see your savings breakdown!</p>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# ─── Aggregate totals ────────────────────────────────────────────────────────
total_original  = sum(e["cost"]["original_cost_usd"] for e in cost_history)
total_savings   = sum(e["cost"]["savings_usd"] for e in cost_history)
total_net       = sum(e["cost"]["your_cost_usd"] for e in cost_history)
total_tokens_in = sum(e["cost"]["input_tokens"] for e in cost_history)
total_tokens_out= sum(e["cost"]["output_tokens"] for e in cost_history)
all_orgs        = [org for e in cost_history for org in e["cost"]["orgs_featured"]]
unique_orgs     = list(dict.fromkeys(all_orgs))  # preserve order, deduplicate
overall_pct     = round((total_savings / total_original * 100), 1) if total_original > 0 else 0

# ─── Summary stat cards ───────────────────────────────────────────────────────
st.markdown('<div class="section-header">📊 Session Summary</div>', unsafe_allow_html=True)

c1, c2, c3, c4, c5 = st.columns(5)

with c1:
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-label">Total Queries</div>
        <div class="stat-value blue">{len(cost_history)}</div>
        <div class="stat-sub">{total_tokens_in + total_tokens_out:,} total tokens</div>
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
    org_pills = "".join(f'<span class="org-pill">{o}</span>' for o in unique_orgs) \
                if unique_orgs else '<span style="color:#555;">none yet</span>'
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-label">Orgs Featured</div>
        <div class="stat-value gold">{len(all_orgs)}</div>
        <div class="stat-sub">{len(unique_orgs)} unique sponsors</div>
    </div>""", unsafe_allow_html=True)

st.markdown("---")

# ─── Pie Chart ───────────────────────────────────────────────────────────────
col_pie, col_bar = st.columns([1, 1], gap="large")

with col_pie:
    st.markdown('<div class="section-header">🥧 Cost vs Savings Breakdown</div>', unsafe_allow_html=True)

    pie_labels = ["You Pay (Net Cost)", "Savings (Sponsored Revenue)"]
    pie_values = [round(total_net, 6), round(total_savings, 6)]
    pie_colors = ["#1E90FF", "#2ECC71"]

    if sum(pie_values) > 0:
        fig_pie = go.Figure(data=[go.Pie(
            labels=pie_labels,
            values=pie_values,
            hole=0.5,
            marker=dict(colors=pie_colors, line=dict(color="#0e1117", width=2)),
            textinfo="label+percent",
            textfont=dict(size=13, color="white"),
            hovertemplate="<b>%{label}</b><br>Amount: $%{value:.6f}<br>Share: %{percent}<extra></extra>",
        )])
        fig_pie.add_annotation(
            text=f"<b>{overall_pct}%</b><br>saved",
            x=0.5, y=0.5,
            font=dict(size=16, color="#2ECC71"),
            showarrow=False
        )
        fig_pie.update_layout(
            paper_bgcolor="#0e1117",
            plot_bgcolor="#0e1117",
            font=dict(color="white", family="Inter"),
            legend=dict(
                bgcolor="#1a1a2e",
                bordercolor="#2a2a4a",
                borderwidth=1,
                font=dict(color="#ccc"),
            ),
            margin=dict(t=10, b=10, l=10, r=10),
            showlegend=True,
            height=340,
        )
        st.plotly_chart(fig_pie, use_container_width=True)
    else:
        st.info("Not enough cost data to render chart.")

# ─── Per-query bar chart ─────────────────────────────────────────────────────
with col_bar:
    st.markdown('<div class="section-header">📈 Cost Per Query</div>', unsafe_allow_html=True)

    query_labels = [f"Q{i+1}" for i in range(len(cost_history))]
    orig_values  = [e["cost"]["original_cost_usd"] for e in cost_history]
    save_values  = [e["cost"]["savings_usd"] for e in cost_history]
    net_values   = [e["cost"]["your_cost_usd"] for e in cost_history]

    fig_bar = go.Figure()
    fig_bar.add_trace(go.Bar(
        name="Original Cost",
        x=query_labels, y=orig_values,
        marker_color="#444", opacity=0.7,
    ))
    fig_bar.add_trace(go.Bar(
        name="You Pay",
        x=query_labels, y=net_values,
        marker_color="#1E90FF",
    ))
    fig_bar.add_trace(go.Bar(
        name="Savings",
        x=query_labels, y=save_values,
        marker_color="#2ECC71",
    ))

    fig_bar.update_layout(
        barmode="group",
        paper_bgcolor="#0e1117",
        plot_bgcolor="#111827",
        font=dict(color="#aaa", family="Inter"),
        xaxis=dict(title="Query", gridcolor="#1f2937"),
        yaxis=dict(title="Cost (USD)", gridcolor="#1f2937", tickformat="$.6f"),
        legend=dict(
            bgcolor="#1a1a2e",
            bordercolor="#2a2a4a",
            borderwidth=1,
            font=dict(color="#ccc"),
        ),
        margin=dict(t=10, b=40, l=10, r=10),
        height=340,
    )
    st.plotly_chart(fig_bar, use_container_width=True)

# ─── Per-query detail table ───────────────────────────────────────────────────
st.markdown('<div class="section-header">📋 Per-Query Breakdown</div>', unsafe_allow_html=True)

rows = []
for i, entry in enumerate(cost_history):
    c = entry["cost"]
    rows.append({
        "#": i + 1,
        "Query": entry.get("prompt_snippet", f"Query {i+1}"),
        "In Tokens": c["input_tokens"],
        "Out Tokens": c["output_tokens"],
        "Original Cost": format_usd(c["original_cost_usd"]),
        "Savings": format_usd(c["savings_usd"]),
        "You Pay": format_usd(c["your_cost_usd"]),
        "Saved %": f"{c['savings_pct']}%",
        "Orgs Featured": ", ".join(c["orgs_featured"]) if c["orgs_featured"] else "—",
    })

df = pd.DataFrame(rows)
st.dataframe(
    df,
    use_container_width=True,
    hide_index=True,
    column_config={
        "#": st.column_config.NumberColumn(width="small"),
        "Query": st.column_config.TextColumn(width="large"),
        "Saved %": st.column_config.TextColumn(width="small"),
        "Orgs Featured": st.column_config.TextColumn(width="medium"),
    }
)

# ─── Org frequency chart ─────────────────────────────────────────────────────
if all_orgs:
    st.markdown('<div class="section-header">🏢 Most-Featured Sponsors This Session</div>', unsafe_allow_html=True)

    from collections import Counter
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
        color_continuous_scale=["#1a1a2e", "#1E90FF"],
        labels={"Times Featured": "# of times featured"},
        text="Times Featured",
    )
    fig_orgs.update_traces(textposition="outside", textfont_color="white")
    fig_orgs.update_layout(
        paper_bgcolor="#0e1117",
        plot_bgcolor="#111827",
        font=dict(color="#aaa", family="Inter"),
        xaxis=dict(gridcolor="#1f2937"),
        yaxis=dict(gridcolor="#1f2937"),
        coloraxis_showscale=False,
        margin=dict(t=10, b=20, l=10, r=60),
        height=max(250, len(org_df) * 42),
    )
    st.plotly_chart(fig_orgs, use_container_width=True)

# ─── Footer ───────────────────────────────────────────────────────────────────
st.markdown("---")
st.caption(
    f"💡 Savings are calculated by offsetting the {GPT52_PRICING['model']} API cost with "
    f"${REVENUE_PER_ORG_USD} revenue per sponsored organisation shown in responses. "
    "Token counts are approximate (word × 1.35 ratio)."
)
