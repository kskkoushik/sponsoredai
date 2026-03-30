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
        margin-bottom: 1rem;
        line-height: 1.6;
    }
    .user-message {
        background-color: #1a1a2e;
        border-left: 4px solid #4CAF50;
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
</style>
""", unsafe_allow_html=True)


def parse_and_colorize(text: str) -> str:
    """
    Parse text and apply color coding.
    - Sponsored content (within [SPONSORED]...[/SPONSORED]) -> Blue
    - Regular content -> Green
    """
    # Pattern to match sponsored content
    pattern = r'\[SPONSORED\](.*?)\[/SPONSORED\]'
    
    # Find all sponsored sections
    parts = []
    last_end = 0
    
    for match in re.finditer(pattern, text, re.DOTALL):
        # Add regular text before this match (in green)
        if match.start() > last_end:
            regular_text = text[last_end:match.start()]
            if regular_text.strip():
                parts.append(f'<span class="regular-text">{regular_text}</span>')
        
        # Add sponsored text (in blue)
        sponsored_text = match.group(1)
        parts.append(f'<span class="sponsored-text">{sponsored_text}</span>')
        
        last_end = match.end()
    
    # Add remaining regular text
    if last_end < len(text):
        remaining = text[last_end:]
        if remaining.strip():
            parts.append(f'<span class="regular-text">{remaining}</span>')
    
    return ''.join(parts)


def display_message(role: str, content: str, is_streaming: bool = False):
    """Display a chat message with proper styling."""
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


def initialize_session_state():
    """Initialize session state variables."""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "llm_service" not in st.session_state:
        st.session_state.llm_service = None
    if "vector_store_initialized" not in st.session_state:
        st.session_state.vector_store_initialized = False


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
        """)
        
        st.markdown("---")
        st.markdown("### 🎨 Color Legend")
        st.markdown("""
        <div class="legend">
            <span class="legend-item"><span class="blue-dot">■</span> Sponsored</span>
            <span class="legend-item"><span class="green-dot">■</span> Regular</span>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.messages = []
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
    
    # Chat history
    for message in st.session_state.messages:
        display_message(message["role"], message["content"])
    
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
                # Update the display with colorized content
                colorized = parse_and_colorize(full_response)
                response_placeholder.markdown(
                    f'<div class="chat-message assistant-message"><strong>AI:</strong><br>{colorized}</div>',
                    unsafe_allow_html=True
                )
            
            # Save to history
            st.session_state.messages.append({"role": "assistant", "content": full_response})
            
        except Exception as e:
            st.error(f"Error generating response: {e}")
            response_placeholder.empty()


if __name__ == "__main__":
    main()

//harish
//today works