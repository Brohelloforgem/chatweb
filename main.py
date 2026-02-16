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

# --- 2. SECURITY & SESSION INITIALIZATION ---
def check_password():
    if "password_correct" not in st.session_state:
        st.session_state.password_correct = False
    
    if st.session_state.password_correct: 
        return True

    st.title("💠 GEM >3 SECURE LINK")
    pwd = st.text_input("Enter Access Key", type="password")
    if st.button("Initialize Neural Link"):
        # Access password from secrets (default to 'admin' if not set)
        if pwd == st.secrets.get("APP_PASSWORD", "admin"):
            st.session_state.password_correct = True
            st.rerun()
        else:
            st.error("Access Denied.")
    return False

# Initialize Session States early to avoid AttributeErrors
if "messages" not in st.session_state: 
    st.session_state.messages = []
if "total_tokens" not in st.session_state: 
    st.session_state.total_tokens = 0

if check_password():
    load_dotenv()
    genai.configure(api_key=os.getenv("GEMINI_API_KEY") or st.secrets.get("GEMINI_API_KEY"))

    # --- 3. SIDEBAR ---
    with st.sidebar:
        st.title("💠 GEM >3 PRO")
        
        st.subheader("🧠 Neural Tuning")
        sys_prompt = st.text_area("System Instructions", 
            value="You are GEM >3, a futuristic AI. Be helpful, concise, and slightly witty.",
            help="Define the bot's personality here.")
        
        st.divider()
        uploaded_file = st.file_uploader("Visual Input", type=["jpg", "png", "jpeg"])
        if uploaded_file: 
            st.image(uploaded_file, use_container_width=True)
        
        st.divider()
        token_display = st.empty()
        token_display.metric("Total Usage", f"{st.session_state.total_tokens:,} tokens")
        
        if st.session_state.messages:
            chat_json = json.dumps(st.session_state.messages, indent=2)
            st.download_button("📂 Export Logs", data=chat_json, file_name="gem3_logs.json", mime="application/json")

        if st.button("🗑️ Reset Link"):
            st.session_state.messages = []
            st.session_state.total_tokens = 0
            st.rerun()

    # --- 4. MODEL & CHAT INITIALIZATION ---
    # Define model and chat session OUTSIDE the chat_input block to avoid NameErrors
    try:
        model = genai.GenerativeModel('gemini-2.0-flash', system_instruction=sys_prompt)
    except:
        # Fallback to 1.5 if 2.0 isn't available in your region yet
        model = genai.GenerativeModel('gemini-1.5-flash-latest', system_instruction=sys_prompt)

    # Format history for the Gemini API
    # Gemini uses 'model' instead of 'assistant'
    api_history = [
        {"role": "user" if m["role"] == "user" else "model", "parts": [m["content"]]}
        for m in st.session_state.messages
    ]
    
    chat_session = model.start_chat(history=api_history)

    # --- 5. CHAT INTERFACE ---
    # Display historical messages
    for msg in st.session_state.messages:
        avatar = "🤖" if msg["role"] == "assistant" else "👤"
        with st.chat_message(msg["role"], avatar=avatar):
            st.markdown(msg["content"])

    # Handle new user input
    if prompt := st.chat_input("Command GEM >3..."):
        # Add user message to UI
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user", avatar="👤"):
            st.markdown(prompt)

        # Generate Assistant Response
        with st.chat_message("assistant", avatar="🤖"):
            with st.status("GEM >3 is processing...", expanded=False) as status:
                try:
                    # Include image in the content list if uploaded
                    content = [prompt, Image.open(uploaded_file)] if uploaded_file else [prompt]
                    
                    placeholder = st.empty()
                    full_response = ""
                    
                    # Stream the response
                    response = chat_session.send_message(content, stream=True)
                    
                    for chunk in response:
                        if chunk.candidates[0].content.parts:
                            full_response += chunk.text
                            placeholder.markdown(full_response + "▌")
                    
                    placeholder.markdown(full_response)
                    
                    # Update usage metrics
                    usage = response.usage_metadata
                    st.session_state.total_tokens += usage.total_token_count
                    token_display.metric("Total Usage", f"{st.session_state.total_tokens:,} tokens")
                    status.update(label=f"Done (+{usage.total_token_count} tokens)", state="complete")
                    
                    # Save assistant message to history
                    st.session_state.messages.append({"role": "assistant", "content": full_response})

                except Exception as e:
                    status.update(label="System Error", state="error")
                    st.error(f"Error: {str(e)}")
