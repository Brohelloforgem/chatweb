import streamlit as st
import google.generativeai as genai
from PIL import Image
import os
from dotenv import load_dotenv

# --- 1. MANDATORY FIRST COMMAND ---
st.set_page_config(page_title="GEM >3", layout="wide", initial_sidebar_state="expanded")

# --- 2. THEME & STYLING (Fixed keyword error) ---
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stChatMessage { border-radius: 15px; border: 1px solid #30363d; background-color: #161b22; }
    /* Glowing effect for the GEM >3 brand */
    .st-emotion-cache-pf561s { color: #00d4ff !important; text-shadow: 0 0 10px #00d4ff; }
    </style>
    """, unsafe_allow_html=True) # FIXED: changed unsafe_allow_code to unsafe_allow_html

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

    # Sidebar UI
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

    # Chat History Setup
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for msg in st.session_state.messages:
        avatar = "🤖" if msg["role"] == "assistant" else "👤"
        with st.chat_message(msg["role"], avatar=avatar):
            st.markdown(msg["content"])

    # User Input & Processing
    if prompt := st.chat_input("Command GEM >3..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user", avatar="👤"):
            st.markdown(prompt)

        with st.chat_message("assistant", avatar="🤖"):
            with st.status("GEM >3 is thinking...", expanded=False) as status:
                try:
                    # Stable 2026 Model Choice
                    model = genai.GenerativeModel('gemini-2.5-flash')
                    
                    content = [prompt, Image.open(uploaded_file)] if uploaded_file else [prompt]
                    response = model.generate_content(content)
                    
                    full_res = response.text
                    tokens = response.usage_metadata.total_token_count
                    
                    st.session_state.total_tokens += tokens
                    status.update(label=f"Response Generated (+{tokens} tokens)", state="complete")
                    
                except Exception as e:
                    status.update(label="System Error", state="error")
                    st.error(f"Neural breakdown: {e}")
                    full_res = "System failed to compute. Verify API Key and try again."

            st.markdown(full_res)
            st.session_state.messages.append({"role": "assistant", "content": full_res})
# ... (Security and Setup code) ...

# 1. INITIALIZE TOTAL TOKENS
if "total_tokens" not in st.session_state:
    st.session_state.total_tokens = 0

# 2. RENDER SIDEBAR AFTER CHAT PROCESSING (OR USE A PLACEHOLDER)
with st.sidebar:
    st.title("💠 GEM >3")
    # We use a placeholder so we can update this metric even if it's "above" the chat in the code
    token_placeholder = st.empty()
    # Initial display
    token_placeholder.metric("Total Tokens", f"{st.session_state.total_tokens:,}")

# ... (Chat Display logic) ...

if prompt := st.chat_input("Command GEM >3..."):
    # ... (Display User Message) ...

    with st.chat_message("assistant"):
        with st.status("Thinking...") as status:
            response = model.generate_content(content)
            new_tokens = response.usage_metadata.total_token_count
            
            # 3. UPDATE THE STATE
            st.session_state.total_tokens += new_tokens
            status.update(label="Complete", state="complete")

        st.markdown(response.text)
        
        # 4. FORCE A REFRESH OF THE SIDEBAR METRIC
        token_placeholder.metric("Total Tokens", f"{st.session_state.total_tokens:,}")
