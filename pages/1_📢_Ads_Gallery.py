"""
Ads Gallery Page - View all sponsored ads in card format.
"""

import streamlit as st
from ads_data import get_all_ads

st.set_page_config(
    page_title="Ads Gallery - Sponsored AI",
    page_icon="📢",
    layout="wide"
)

# Custom CSS for cards
st.markdown("""
<style>
    .ad-card {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        border-left: 4px solid #1E90FF;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .ad-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0, 0, 0, 0.4);
    }
    .company-name {
        color: #1E90FF;
        font-size: 1.4rem;
        font-weight: bold;
        margin-bottom: 0.5rem;
    }
    .category-badge {
        display: inline-block;
        background-color: #2ECC71;
        color: #0e1117;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
        margin-bottom: 0.75rem;
    }
    .ad-text {
        color: #e0e0e0;
        line-height: 1.6;
        font-size: 1rem;
    }
    .keywords-container {
        margin-top: 1rem;
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
    }
    .keyword-tag {
        background-color: rgba(30, 144, 255, 0.2);
        color: #1E90FF;
        padding: 0.2rem 0.5rem;
        border-radius: 4px;
        font-size: 0.75rem;
    }
    .stats-box {
        background: linear-gradient(135deg, #16213e 0%, #1a1a2e 100%);
        border-radius: 10px;
        padding: 1rem;
        text-align: center;
        margin-bottom: 1rem;
    }
    .stats-number {
        font-size: 2rem;
        font-weight: bold;
        color: #1E90FF;
    }
    .stats-label {
        color: #888;
        font-size: 0.9rem;
    }
</style>
""", unsafe_allow_html=True)

st.title("📢 Ads Gallery")
st.markdown("*Browse all sponsored ads available in the system*")

# Get all ads
ads = get_all_ads()

# Calculate stats
categories = list(set(ad["category"] for ad in ads))
companies = list(set(ad["company"] for ad in ads))

# Stats row
col1, col2, col3 = st.columns(3)
with col1:
    st.markdown(f"""
    <div class="stats-box">
        <div class="stats-number">{len(ads)}</div>
        <div class="stats-label">Total Ads</div>
    </div>
    """, unsafe_allow_html=True)
with col2:
    st.markdown(f"""
    <div class="stats-box">
        <div class="stats-number">{len(categories)}</div>
        <div class="stats-label">Categories</div>
    </div>
    """, unsafe_allow_html=True)
with col3:
    st.markdown(f"""
    <div class="stats-box">
        <div class="stats-number">{len(companies)}</div>
        <div class="stats-label">Companies</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# Filter by category
selected_category = st.selectbox(
    "Filter by Category",
    ["All"] + sorted(categories),
    index=0
)

# Filter ads
if selected_category != "All":
    filtered_ads = [ad for ad in ads if ad["category"] == selected_category]
else:
    filtered_ads = ads

st.markdown(f"*Showing {len(filtered_ads)} ads*")

# Display ads in grid
cols = st.columns(2)

for i, ad in enumerate(filtered_ads):
    with cols[i % 2]:
        keywords_html = "".join([
            f'<span class="keyword-tag">{kw}</span>' 
            for kw in ad["keywords"][:5]  # Show max 5 keywords
        ])
        
        st.markdown(f"""
        <div class="ad-card">
            <div class="company-name">{ad["company"]}</div>
            <span class="category-badge">{ad["category"]}</span>
            <div class="ad-text">{ad["ad_text"]}</div>
            <div class="keywords-container">
                {keywords_html}
            </div>
        </div>
        """, unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown("*These ads are retrieved via RAG when users ask relevant questions.*")
