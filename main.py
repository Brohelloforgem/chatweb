import streamlit as st
import google.generativeai as genai
from PIL import Image
import pypdf # UPDATED: Modern library replaces PyPDF2
import os
import json
from dotenv import load_dotenv

# --- 1. MANDATORY FIRST COMMAND ---
st.set_page_config(page_title="GEM >3 Ultimate", layout="wide", initial_sidebar_state="expanded")

# --- 2. THEME & STYLING ---
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stChatMessage { border-radius: 15px; border: 1px solid #30363d; background-color: #161b22; transition: all 0.3s ease; }
    .stChatMessage:hover { border-color: #00d4ff; box-shadow: 0 0 10px rgba(0, 212, 255, 0.2); }
    .st-emotion-cache-pf561s { color: #00d4ff !important; text-shadow: 0 0 10px #00d4ff; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. HELPER FUNCTIONS ---
def extract_text_from_pdf(uploaded_file):
    reader = pypdf.PdfReader(uploaded_file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
    return text

# --- 4. INITIALIZATION ---
if "messages" not in st.session_state: st.session_state.messages = []
if "total_tokens" not in st.session_state: st.session_state.total_tokens = 0

api_key = st.secrets.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")
if not api_key:
    st.error("Missing API Key. Add it to Streamlit Secrets!")
    st.stop()
genai.configure(api_key=api_key)

# --- 5. SIDEBAR ---
with st.sidebar:
    st.title("💠 GEM >3 ULTIMATE")
    persona = st.selectbox("Neural Personality", ["Assistant", "Data Analyst", "Creative", "Coder"])
    
    st.divider()
    uploaded_file = st.file_uploader("Upload Image or PDF", type=["jpg", "png", "jpeg", "pdf"])
    file_context = ""
    
    if uploaded_file:
        if uploaded_file.type == "application/pdf":
            file_context = extract_text_from_pdf(uploaded_file)
            st.success(f"PDF Context Sync: {len(file_context)} chars")
        else:
            st.image(uploaded_file, caption="Visual Data Ready", width='stretch')

    st.divider()
    token_display = st.empty()
    token_display.metric("Total Tokens", f"{st.session_state.total_tokens:,}")
    
    if st.button("🗑️ Reset Neural Link"):
        st.session_state.messages = []
        st.session_state.total_tokens = 0
        st.rerun()

# --- 6. CHAT INTERFACE ---
for msg in st.session_state.messages:
    avatar = "🤖" if msg["role"] == "assistant" else "👤"
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])

# New 2026 Feature: Native Voice Input
audio_data = st.audio_input("Record Voice Command")
prompt = st.chat_input("Command GEM >3...")

if audio_data and not prompt:
    prompt = "Analyzing voice command... [Audio signal received]"

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    with st.chat_message("assistant", avatar="🤖"):
        with st.status("GEM >3 is processing...", expanded=False) as status:
            try:
                # 2026 Stable Model with System Instructions
                model = genai.GenerativeModel('gemini-2.5-flash')
                
                # Build context
                full_query = f"CONTEXT FROM FILE: {file_context}\n\nUSER PROMPT: {prompt}" if file_context else prompt
                inputs = [full_query]
                if uploaded_file and uploaded_file.type != "application/pdf":
                    inputs.append(Image.open(uploaded_file))
                
                # Streaming Response
                placeholder = st.empty()
                full_response = ""
                response = model.generate_content(inputs, stream=True)
                
                for chunk in response:
                    full_response += chunk.text
                    placeholder.markdown(full_response + "▌")
                
                placeholder.markdown(full_response)
                
                # Update Stats
                st.session_state.total_tokens += response.usage_metadata.total_token_count
                token_display.metric("Total Tokens", f"{st.session_state.total_tokens:,}")
                status.update(label="Sync Successful", state="complete")
                
                st.session_state.messages.append({"role": "assistant", "content": full_response})

            except Exception as e:
                status.update(label="Critical System Error", state="error")
                st.error(f"Neural breakdown: {e}")
