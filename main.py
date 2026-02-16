import streamlit as st
import google.generativeai as genai
from PIL import Image
import os
import json
from dotenv import load_dotenv

# --- 1. CONFIG & STYLING ---
st.set_page_config(page_title="GEM >3 Pro", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stChatMessage { border-radius: 15px; border: 1px solid #30363d; background-color: #161b22; }
    .st-emotion-cache-pf561s { color: #00d4ff !important; text-shadow: 0 0 10px #00d4ff; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. SECURITY ---
def check_password():
    if "password_correct" not in st.session_state:
        st.session_state.password_correct = False
    if st.session_state.password_correct: return True

    st.title("💠 GEM >3 SECURE LINK")
    pwd = st.text_input("Enter Access Key", type="password")
    if st.button("Initialize Neural Link"):
        if pwd == st.secrets.get("APP_PASSWORD", "admin"):
            st.session_state.password_correct = True
            st.rerun()
        else:
            st.error("Access Denied.")
    return False

if check_password():
    load_dotenv()
    genai.configure(api_key=os.getenv("GEMINI_API_KEY") or st.secrets.get("GEMINI_API_KEY"))

    # Session Initialization
    if "messages" not in st.session_state: st.session_state.messages = []
    if "total_tokens" not in st.session_state: st.session_state.total_tokens = 0

    # --- 3. SIDEBAR: NEW FEATURES ---
    with st.sidebar:
        st.title("💠 GEM >3 PRO")
        
        # FEATURE 1: System Prompt (Personality)
        st.subheader("🧠 Neural Tuning")
        sys_prompt = st.text_area("System Instructions", 
            value="You are GEM >3, a futuristic AI. Be helpful, concise, and slightly witty.",
            help="Define the bot's personality here.")
        
        st.divider()
        uploaded_file = st.file_uploader("Visual Input", type=["jpg", "png", "jpeg"])
        if uploaded_file: st.image(uploaded_file, width='stretch')
        
        st.divider()
        token_display = st.empty()
        token_display.metric("Total Usage", f"{st.session_state.total_tokens:,} tokens")
        
        # FEATURE 2: Export Chat
        if st.session_state.messages:
            chat_json = json.dumps(st.session_state.messages, indent=2)
            st.download_button("📂 Export Logs", data=chat_json, file_name="gem3_logs.json", mime="application/json")

        if st.button("🗑️ Reset Link"):
            st.session_state.messages = []
            st.session_state.total_tokens = 0
            st.rerun()

    # --- 4. CHAT INTERFACE ---
    for msg in st.session_state.messages:
        avatar = "🤖" if msg["role"] == "assistant" else "👤"
        with st.chat_message(msg["role"], avatar=avatar):
            st.markdown(msg["content"])

    if prompt := st.chat_input("Command GEM >3..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user", avatar="👤"):
            st.markdown(prompt)

        with st.chat_message("assistant", avatar="🤖"):
            # Use 'status' for modern loading
            with st.status("GEM >3 is processing...", expanded=False) as status:
                try:
                    # Model Fallback Logic (2026 Stable)
                    try:
                        model = genai.GenerativeModel('gemini-2.5-flash', system_instruction=sys_prompt)
                    except:
                        model = genai.GenerativeModel('gemini-1.5-flash-latest', system_instruction=sys_prompt)
                    
                    content = [prompt, Image.open(uploaded_file)] if uploaded_file else [prompt]
                    
                    # FEATURE 3: STREAMING
                    placeholder = st.empty()
                    full_response = ""
                    
                    # Generate with stream=True
                    response = model.generate_content(content, stream=True)
                    
                    for chunk in response:
                        full_response += chunk.text
                        placeholder.markdown(full_response + "▌") # Typing cursor effect
                    
                    placeholder.markdown(full_response) # Final clean render
                    
                    # Token Update
                    usage = response.usage_metadata
                    st.session_state.total_tokens += usage.total_token_count
                    token_display.metric("Total Usage", f"{st.session_state.total_tokens:,} tokens")
                    status.update(label=f"Done (+{usage.total_token_count} tokens)", state="complete")
                    
                    st.session_state.messages.append({"role": "assistant", "content": full_response})

                except Exception as e:
                    status.update(label="System Error", state="error")
                    st.error(f"Error: {e}")
# --- 4. CHAT INTERFACE ---
if st.session_state.password_correct:  # Ensure we only run this if logged in
    
    # 1. Initialize the Chat History for the API
    # Move this INSIDE the authenticated block
    history = [
        {"role": "user" if m["role"] == "user" else "model", "parts": [m["content"]]}
        for m in st.session_state.messages
    ]

    # 2. Initialize the model and chat session
    # Use the model defined in your sidebar or re-define here
    chat_session = model.start_chat(history=history)

    # 3. Display existing messages
    for msg in st.session_state.messages:
        avatar = "🤖" if msg["role"] == "assistant" else "👤"
        with st.chat_message(msg["role"], avatar=avatar):
            st.markdown(msg["content"])

    # 4. Handle new input
    if prompt := st.chat_input("Command GEM >3..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user", avatar="👤"):
            st.markdown(prompt)

        with st.chat_message("assistant", avatar="🤖"):
            with st.status("GEM >3 is processing...", expanded=False) as status:
                try:
                    content = [prompt, Image.open(uploaded_file)] if uploaded_file else prompt
                    
                    placeholder = st.empty()
                    full_response = ""
                    
                    response = chat_session.send_message(content, stream=True)
                    
                    for chunk in response:
                        if chunk.candidates[0].content.parts:
                            full_response += chunk.text
                            placeholder.markdown(full_response + "▌")
                    
                    placeholder.markdown(full_response)
                    
                    # Update metrics
                    usage = response.usage_metadata
                    st.session_state.total_tokens += usage.total_token_count
                    token_display.metric("Total Usage", f"{st.session_state.total_tokens:,} tokens")
                    status.update(label=f"Done (+{usage.total_token_count} tokens)", state="complete")
                    
                    st.session_state.messages.append({"role": "assistant", "content": full_response})

                except Exception as e:
                    status.update(label="System Error", state="error")
                    st.error(f"Error: {e}")
