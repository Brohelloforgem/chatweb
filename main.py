import streamlit as st
import google.generativeai as genai
from PIL import Image
import os
import json
from dotenv import load_dotenv

# --- 1. MANDATORY FIRST COMMAND ---
st.set_page_config(page_title="GEM >3 Lite", layout="wide", initial_sidebar_state="expanded")

# --- 2. THEME & STYLING ---
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stChatMessage { border-radius: 15px; border: 1px solid #30363d; background-color: #161b22; }
    .st-emotion-cache-pf561s { color: #00d4ff !important; text-shadow: 0 0 10px #00d4ff; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. INITIALIZATION ---
load_dotenv()
if "messages" not in st.session_state: st.session_state.messages = []
if "total_tokens" not in st.session_state: st.session_state.total_tokens = 0

api_key = st.secrets.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")
if not api_key:
    st.error("Missing API Key. Add it to Streamlit Secrets!")
    st.stop()
genai.configure(api_key=api_key)

# --- 4. SIDEBAR ---
with st.sidebar:
    st.title("💠 GEM >3 LITE")
    st.caption("Stable Text & Vision v2.6")
    
    st.divider()
    # Simplified Uploader: Images only
    uploaded_file = st.file_uploader("Visual Input", type=["jpg", "png", "jpeg"])
    if uploaded_file:
        st.image(uploaded_file, caption="Vision Ready", width='stretch')

    st.divider()
    token_display = st.empty()
    token_display.metric("Total Tokens", f"{st.session_state.total_tokens:,}")
    
    if st.button("🗑️ Reset Link"):
        st.session_state.messages = []
        st.session_state.total_tokens = 0
        st.rerun()

# --- 5. CHAT INTERFACE ---
for msg in st.session_state.messages:
    avatar = "🤖" if msg["role"] == "assistant" else "👤"
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])

if prompt := st.chat_input("Command GEM >3..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    with st.chat_message("assistant", avatar="🤖"):
        with st.status("GEM >3 is thinking...", expanded=False) as status:
            try:
                # 2026 Stable Model
                model = genai.GenerativeModel('gemini-2.0-flash')
                
                inputs = [prompt]
                if uploaded_file:
                    inputs.append(Image.open(uploaded_file))
                
                placeholder = st.empty()
                full_response = ""
                response = model.generate_content(inputs, stream=True)
                
                for chunk in response:
                    full_response += chunk.text
                    placeholder.markdown(full_response + "▌")
                
                placeholder.markdown(full_response)
                
                # Update Token Count
                st.session_state.total_tokens += response.usage_metadata.total_token_count
                token_display.metric("Total Tokens", f"{st.session_state.total_tokens:,}")
                status.update(label="Sync Complete", state="complete")
                
                st.session_state.messages.append({"role": "assistant", "content": full_response})

            except Exception as e:
                status.update(label="System Error", state="error")
                st.error(f"Error: {e}")
