import streamlit as st
import google.generativeai as genai
from PIL import Image
import os
from dotenv import load_dotenv

# --- 1. MANDATORY FIRST COMMAND ---
st.set_page_config(page_title="GEM >3", layout="wide", initial_sidebar_state="expanded")

# --- 2. THEME & STYLING ---
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stChatMessage { border-radius: 15px; border: 1px solid #30363d; background-color: #161b22; }
    /* Glowing effect for the GEM >3 brand */
    .st-emotion-cache-1c7n2ka { color: #00d4ff !important; text-shadow: 0 0 10px #00d4ff; }
    </style>
    """, unsafe_allow_code=True)

# --- 3. SECURITY GATE ---
def check_password():
    if "password_correct" not in st.session_state:
        st.session_state.password_correct = False
    if st.session_state.password_correct:
        return True

    st.title("💠 GEM >3 SECURE LINK")
    pwd = st.text_input("Enter Access Key", type="password")
    if st.button("Initialize Neural Link"):
        if pwd == st.secrets.get("APP_PASSWORD", "admin"):
            st.session_state.password_correct = True
            st.rerun()
        else:
            st.error("Access Denied.")
    return False

# --- 4. MAIN APP LOGIC ---
if check_password():
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY") or st.secrets.get("GEMINI_API_KEY")
    genai.configure(api_key=api_key)

    # Initialize Sidebar
    with st.sidebar:
        st.title("💠 GEM >3")
        st.caption("AI Vision & Cognition v2.6")
        
        st.divider()
        uploaded_file = st.file_uploader("Visual Input (Images)", type=["jpg", "png", "jpeg"])
        if uploaded_file:
            st.image(uploaded_file, width='stretch')
        
        st.divider()
        if "total_tokens" not in st.session_state: st.session_state.total_tokens = 0
        st.metric("Total Usage", f"{st.session_state.total_tokens:,} tokens")
        
        if st.button("🗑️ Reset Link"):
            st.session_state.messages = []
            st.session_state.total_tokens = 0
            st.rerun()

    # Chat History
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # User Input
    if prompt := st.chat_input("Command GEM >3..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            # Using st.status for a modern 2026 loading experience
            with st.status("GEM >3 is thinking...", expanded=False) as status:
                try:
                    # UPDATED: gemini-2.0-flash is the 2026 stable name
                    model = genai.GenerativeModel('gemini-2.0-flash')
                    
                    content = [prompt, Image.open(uploaded_file)] if uploaded_file else [prompt]
                    response = model.generate_content(content)
                    
                    full_res = response.text
                    tokens = response.usage_metadata.total_token_count
                    
                    st.session_state.total_tokens += tokens
                    status.update(label=f"Response Generated (+{tokens} tokens)", state="complete")
                    
                except Exception as e:
                    status.update(label="System Error", state="error")
                    st.error(f"Neural breakdown: {e}")
                    full_res = "I encountered an error. Please try again."

            st.markdown(full_res)
            st.session_state.messages.append({"role": "assistant", "content": full_res})
