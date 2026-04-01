"""
Sponsored AI - Streamlit Application
A chatbot that blends sponsored ads into responses using RAG.
"""

import streamlit as st
import re
import os
from dotenv import load_dotenv
from vector_store import search_ads, get_vector_store
from llm_service import create_llm_service
from cost_calculator import calculate_message_cost, format_usd, REVENUE_PER_ORG_USD, GPT52_PRICING

# Load environment variables from .env file
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="Sponsored AI",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for color coding
st.markdown("""
<style>
    .sponsored-text {
        color: #1E90FF !important;
        font-weight: 500;
    }
    .regular-text {
        color: #2ECC71 !important;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 0.5rem;
        line-height: 1.6;|
        
    }
    .user-message {
        background-color: #1a1a2e;
        border-left: 4px solid #4CAF50;
        color: white;    
    }
    .assistant-message {
        background-color: #16213e;
        border-left: 4px solid #2196F3;
    }
    .stTextInput > div > div > input {
        caret-color: white;
    }
    .legend {
        padding: 0.5rem 1rem;
        background-color: #0e1117;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    .legend-item {
        display: inline-block;
        margin-right: 1.5rem;
    }
    .blue-dot {
        color: #1E90FF;
        font-weight: bold;
    }
    .green-dot {
        color: #2ECC71;
        font-weight: bold;
    }
    /* Cost metadata card */
    .cost-meta {
        background: linear-gradient(135deg, #0d1117 0%, #1a1a2e 100%);
        border: 1px solid #2a2a4a;
        border-radius: 8px;
        padding: 0.65rem 1rem;
        margin-top: 0.25rem;
        margin-bottom: 1rem;
        font-size: 0.82rem;
        display: flex;
        flex-wrap: wrap;
        gap: 1rem;
        align-items: center;
    }
    .cost-meta-item {
        display: flex;
        flex-direction: column;
        min-width: 90px;
    }
    .cost-meta-label {
        color: #666;
        font-size: 0.7rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .cost-meta-value {
        color: #ccc;
        font-weight: 600;
        font-size: 0.85rem;
    }
    .cost-meta-value.savings {
        color: #2ECC71;
    }
    .cost-meta-value.original {
        color: #888;
        text-decoration: line-through;
    }
    .cost-meta-value.net {
        color: #1E90FF;
    }
    .org-chip {
        display: inline-block;
        background: rgba(30,144,255,0.15);
        color: #5aabff;
        border-radius: 4px;
        padding: 1px 6px;
        margin: 1px;
        font-size: 0.72rem;
    }
    .powered-by {
        font-size: 0.68rem;
        color: #444;
        border-top: 1px solid #222;
        padding-top: 0.3rem;
        margin-top: 0.3rem;
        width: 100%;
    }
</style>
""", unsafe_allow_html=True)


def parse_and_colorize(text: str) -> str:
    """
    Parse text and apply color coding.
    - Sponsored content (within [SPONSORED]...[/SPONSORED]) -> Blue
    - Regular content -> Green
    """
    pattern = r'\[SPONSORED\](.*?)\[/SPONSORED\]'

    parts = []
    last_end = 0

    for match in re.finditer(pattern, text, re.DOTALL):
        if match.start() > last_end:
            regular_text = text[last_end:match.start()]
            if regular_text.strip():
                parts.append(f'<span class="regular-text">{regular_text}</span>')

        sponsored_text = match.group(1)
        parts.append(f'<span class="sponsored-text">{sponsored_text}</span>')

        last_end = match.end()

    if last_end < len(text):
        remaining = text[last_end:]
        if remaining.strip():
            parts.append(f'<span class="regular-text">{remaining}</span>')

    return ''.join(parts)


def render_cost_metadata(cost: dict):
    """Render a compact cost metadata bar below an AI response."""
    orgs = cost.get("orgs_featured", [])
    orgs_html = "".join(f'<span class="org-chip">{o}</span>' for o in orgs) if orgs else \
                '<span style="color:#555;">none detected</span>'

    savings_label = f'+{format_usd(cost["savings_usd"])} saved' if cost["savings_usd"] > 0 else "no savings"

    st.markdown(f"""
    <div class="cost-meta">
      <div class="cost-meta-item">
        <span class="cost-meta-label">⚙️ Model</span>
        <span class="cost-meta-value">{GPT52_PRICING['model']}</span>
      </div>
      <div class="cost-meta-item">
        <span class="cost-meta-label">🔢 Tokens</span>
        <span class="cost-meta-value">{cost['input_tokens']} in · {cost['output_tokens']} out</span>
      </div>
      <div class="cost-meta-item">
        <span class="cost-meta-label">💸 Original Cost</span>
        <span class="cost-meta-value original">{format_usd(cost['original_cost_usd'])}</span>
      </div>
      <div class="cost-meta-item">
        <span class="cost-meta-label">💚 You Pay</span>
        <span class="cost-meta-value net">{format_usd(cost['your_cost_usd'])}</span>
      </div>
      <div class="cost-meta-item">
        <span class="cost-meta-label">🏷️ Savings</span>
        <span class="cost-meta-value savings">{savings_label} ({cost['savings_pct']}%)</span>
      </div>
      <div class="cost-meta-item" style="min-width:160px;">
        <span class="cost-meta-label">🏢 Sponsored Orgs</span>
        <span class="cost-meta-value">{orgs_html}</span>
      </div>
      <div class="powered-by">
        Pricing: ${GPT52_PRICING['input_per_1m_tokens']}/1M input · ${GPT52_PRICING['output_per_1m_tokens']}/1M output &nbsp;|&nbsp;
        Revenue: ${REVENUE_PER_ORG_USD}/org shown
      </div>
    </div>
    """, unsafe_allow_html=True)


def display_message(role: str, content: str, cost: dict | None = None):
    """Display a chat message with proper styling and optional cost metadata."""
    if role == "user":
        st.markdown(
            f'<div class="chat-message user-message"><strong>You:</strong><br>{content}</div>',
            unsafe_allow_html=True
        )
    else:
        colorized = parse_and_colorize(content)
        st.markdown(
            f'<div class="chat-message assistant-message"><strong>AI:</strong><br>{colorized}</div>',
            unsafe_allow_html=True
        )
        if cost:
            render_cost_metadata(cost)


def initialize_session_state():
    """Initialize session state variables."""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "llm_service" not in st.session_state:
        st.session_state.llm_service = None
    if "vector_store_initialized" not in st.session_state:
        st.session_state.vector_store_initialized = False
    if "cost_history" not in st.session_state:
        # Each entry: {prompt, response_snippet, cost_dict}
        st.session_state.cost_history = []


def main():
    """Main application function."""
    initialize_session_state()

    # Get API key from environment variable
    api_key = os.getenv("GROQ_API_KEY")

    # Sidebar
    with st.sidebar:
        st.title("🎯 Sponsored AI")
        st.markdown("---")

        # Show API key status
        if api_key:
            st.success("✅ API Key loaded from .env")
        else:
            st.error("❌ GROQ_API_KEY not found in .env file")
            st.info("Add `GROQ_API_KEY=your_key` to .env file")

        # Initialize LLM service
        if api_key and st.session_state.llm_service is None:
            with st.spinner("Initializing AI..."):
                st.session_state.llm_service = create_llm_service(api_key)
                if st.session_state.llm_service:
                    st.success("✅ AI Ready!")
                else:
                    st.error("❌ Failed to initialize AI")

        # Initialize vector store
        if not st.session_state.vector_store_initialized:
            with st.spinner("Loading ad database..."):
                try:
                    get_vector_store()
                    st.session_state.vector_store_initialized = True
                except Exception as e:
                    st.error(f"Failed to load ads: {e}")

        st.markdown("---")
        st.markdown("### 📊 How it works")
        st.markdown("""
        1. Enter your query below
        2. AI finds relevant sponsored content
        3. Response blends info with sponsors
        4. Sponsors offset your API cost!
        """)

        st.markdown("---")
        st.markdown("### 🎨 Color Legend")
        st.markdown("""
        <div class="legend">
            <span class="legend-item"><span class="blue-dot">■</span> Sponsored</span>
            <span class="legend-item"><span class="green-dot">■</span> Regular</span>
        </div>
        """, unsafe_allow_html=True)

        # Session cost summary in sidebar
        if st.session_state.cost_history:
            st.markdown("---")
            st.markdown("### 💰 Session Savings")
            total_orig = sum(c["cost"]["original_cost_usd"] for c in st.session_state.cost_history)
            total_savings = sum(c["cost"]["savings_usd"] for c in st.session_state.cost_history)
            total_net = sum(c["cost"]["your_cost_usd"] for c in st.session_state.cost_history)
            st.metric("Original Cost", format_usd(total_orig))
            st.metric("You Pay", format_usd(total_net), delta=f"-{format_usd(total_savings)}", delta_color="normal")

        st.markdown("---")
        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.messages = []
            st.session_state.cost_history = []
            st.rerun()

    # Main content
    st.title("💬 Sponsored AI Chat")
    st.markdown("*Ask me anything - I'll provide helpful answers with relevant sponsored content!*")

    # Legend in main area
    st.markdown("""
    <div style="display: flex; gap: 2rem; margin-bottom: 1rem; padding: 0.5rem; background: #1a1a2e; border-radius: 0.5rem;">
        <span><span style="color: #1E90FF; font-weight: bold;">●</span> Sponsored Content</span>
        <span><span style="color: #2ECC71; font-weight: bold;">●</span> Regular Content</span>
    </div>
    """, unsafe_allow_html=True)

    # Chat history – render messages paired with their cost metadata
    cost_map = {c["msg_index"]: c["cost"] for c in st.session_state.cost_history}
    assistant_idx = 0
    for message in st.session_state.messages:
        if message["role"] == "user":
            display_message("user", message["content"])
        else:
            cost = cost_map.get(assistant_idx)
            display_message("assistant", message["content"], cost=cost)
            assistant_idx += 1

    # Chat input
    if prompt := st.chat_input("Ask me anything..."):
        if not api_key:
            st.error("⚠️ GROQ_API_KEY not found in .env file!")
            return

        if st.session_state.llm_service is None:
            st.error("⚠️ AI service not initialized. Please check your API key.")
            return

        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        display_message("user", prompt)

        # Search for relevant ads
        with st.spinner("Finding relevant content..."):
            relevant_ads = search_ads(prompt, n_results=2)

        # Generate streaming response
        response_placeholder = st.empty()
        full_response = ""

        try:
            for chunk in st.session_state.llm_service.generate_stream(prompt, relevant_ads):
                full_response += chunk
                colorized = parse_and_colorize(full_response)
                response_placeholder.markdown(
                    f'<div class="chat-message assistant-message"><strong>AI:</strong><br>{colorized}</div>',
                    unsafe_allow_html=True
                )

            # Compute cost metadata
            cost = calculate_message_cost(prompt, full_response)

            # Save to history
            assistant_msg_index = len([m for m in st.session_state.messages if m["role"] == "assistant"])
            st.session_state.messages.append({"role": "assistant", "content": full_response})
            st.session_state.cost_history.append({
                "msg_index": assistant_msg_index,
                "prompt_snippet": prompt[:80] + ("…" if len(prompt) > 80 else ""),
                "cost": cost,
            })

            # Render cost metadata immediately below the response
            render_cost_metadata(cost)

        except Exception as e:
            st.error(f"Error generating response: {e}")
            response_placeholder.empty()


if __name__ == "__main__":
    main()
