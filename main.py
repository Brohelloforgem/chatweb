import streamlit as st
import google.generativeai as genai
from PIL import Image
import os
from dotenv import load_dotenv

# --- 1. CONFIG & THEME ---
load_dotenv()
st.set_page_config(page_title="GEM >3", layout="wide", initial_sidebar_state="expanded")

# Custom CSS for that "GEM >3" futuristic glow
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stChatMessage { border-radius: 15px; margin-bottom: 10px; border: 1px solid #30363d; }
    .st-emotion-cache-1c7n2ka { color: #00d4ff; font-weight: bold; } /* Bot Name Glow */
    </style>
    """, unsafe_allow_code=True)

# --- 2. SECURITY ---
def check_password():
    if "password_correct" not in st.session_state:
        st.session_state.password_correct = False
    if st.session_state.password_correct: return True

    st.title("🔐 GEM >3 ACCESS")
    pwd = st.text_input("Security Key", type="password")
    if st.button("Unlock System"):
        if pwd == st.secrets.get("APP_PASSWORD", "admin"):
            st.session_state.password_correct = True
            st.rerun()
        else:
            st.error("Invalid Key.")
    return False

if check_password():
    # Setup API
    api_key = os.getenv("GEMINI_API_KEY") or st.secrets.get("GEMINI_API_KEY")
    genai.configure(api_key=api_key)

    # --- 3. SIDEBAR UI ---
    with st.sidebar:
        st.title("💠 GEM >3")
        st.caption("v2.6 Stable Build")
        
        # New 2026 Logo Component
        st.logo("https://cdn-icons-png.flaticon.com/512/2103/2103633.png", icon_image="https://cdn-icons-png.flaticon.com/512/2103/2103633.png")
        
        st.divider()
        uploaded_file = st.file_uploader("Drop Image for Vision Analysis", type=["jpg", "png", "jpeg"])
        if uploaded_file:
            st.image(uploaded_file, width='stretch')
        
        st.divider()
        st.subheader("📊 Session Telemetry")
        if "total_tokens" not in st.session_state: st.session_state.total_tokens = 0
        st.metric("Tokens Consumed", f"{st.session_state.total_tokens:,}")
        
        if st.button("🗑️ Clear Neural Link (Reset)"):
            st.session_state.messages = []
            st.session_state.total_tokens = 0
            st.rerun()

    # --- 4. CHAT INTERFACE ---
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display Chat History
    for msg in st.session_state.messages:
        avatar = "🤖" if msg["role"] == "assistant" else "👤"
        with st.chat_message(msg["role"], avatar=avatar):
            st.markdown(msg["content"])

    # Chat Input
    if prompt := st.chat_input("Command GEM >3..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user", avatar="👤"):
            st.markdown(prompt)

        with st.chat_message("assistant", avatar="🤖"):
            # Use 'status' for a 2026-style thinking indicator
            with st.status("GEM >3 is processing...", expanded=False) as status:
                try:
                    # UPDATED: gemini-2.0-flash is the stable 2026 standard
                    model = genai.GenerativeModel('gemini-2.0-flash')
                    
                    content = [prompt, Image.open(uploaded_file)] if uploaded_file else [prompt]
                    response = model.generate_content(content)
                    
                    full_res = response.text
                    tokens = response.usage_metadata.total_token_count
                    
                    st.session_state.total_tokens += tokens
                    status.update(label=f"Analysis Complete (+{tokens} tokens)", state="complete")
                except Exception as e:
                    status.update(label="System Error", state="error")
                    st.error(f"Neural Link Failed: {e}")
                    full_res = "Critical Failure. Check Logs."

            st.markdown(full_res)
            st.session_state.messages.append({"role": "assistant", "content": full_res})
