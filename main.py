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
    /* GEM >3 branding glow */
    .st-emotion-cache-pf561s { color: #00d4ff !important; text-shadow: 0 0 10px #00d4ff; }
    </style>
    """, unsafe_allow_html=True)

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

    # Initialize State Variables
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "total_tokens" not in st.session_state:
        st.session_state.total_tokens = 0

    # SIDEBAR UI
    with st.sidebar:
        st.title("💠 GEM >3")
        st.caption("AI Vision & Cognition v2.6")
        
        st.divider()
        uploaded_file = st.file_uploader("Visual Input (Images)", type=["jpg", "png", "jpeg"])
        if uploaded_file:
            # width='stretch' is the new 2026 standard
            st.image(uploaded_file, width='stretch')
        
        st.divider()
        st.subheader("📊 Session Stats")
        # Placeholder for real-time token updates
        token_display = st.empty() 
        token_display.metric("Total Usage", f"{st.session_state.total_tokens:,} tokens")
        
        if st.button("🗑️ Reset Link"):
            st.session_state.messages = []
            st.session_state.total_tokens = 0
            st.rerun()

    # DISPLAY CHAT HISTORY
    for msg in st.session_state.messages:
        avatar = "🤖" if msg["role"] == "assistant" else "👤"
        with st.chat_message(msg["role"], avatar=avatar):
            st.markdown(msg["content"])

    # USER INPUT & AI PROCESSING
    if prompt := st.chat_input("Command GEM >3..."):
        # Store and display user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user", avatar="👤"):
            st.markdown(prompt)

        # Generate Assistant Response
        with st.chat_message("assistant", avatar="🤖"):
            with st.status("GEM >3 is thinking...", expanded=False) as status:
                try:
                    # MODEL AUTO-FALLBACK: Try newest 2026 model, fallback to LTS
                    try:
                        model = genai.GenerativeModel('gemini-2.5-flash')
                        # Minor check to see if model exists
                        temp_content = ["test"]
                        model.generate_content(temp_content)
                    except:
                        model = genai.GenerativeModel('gemini-1.5-flash-latest')
                    
                    # Prepare content
                    content = [prompt, Image.open(uploaded_file)] if uploaded_file else [prompt]
                    response = model.generate_content(content)
                    
                    full_res = response.text
                    new_tokens = response.usage_metadata.total_token_count
                    
                    # UPDATE STATE & UI
                    st.session_state.total_tokens += new_tokens
                    token_display.metric("Total Usage", f"{st.session_state.total_tokens:,} tokens")
                    
                    status.update(label=f"Computed (+{new_tokens} tokens)", state="complete")
                    
                except Exception as e:
                    status.update(label="System Error", state="error")
                    st.error(f"Neural breakdown: {e}")
                    full_res = "I couldn't process that. Please check your API key or image format."

            st.markdown(full_res)
            st.session_state.messages.append({"role": "assistant", "content": full_res})
