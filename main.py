import streamlit as st
import google.generativeai as genai
from PIL import Image
import PyPDF2 # New requirement: pip install PyPDF2
import os
import json
from dotenv import load_dotenv

# --- 1. CONFIG & STYLING ---
st.set_page_config(page_title="GEM >3 Ultimate", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stChatMessage { border-radius: 15px; border: 1px solid #30363d; background-color: #161b22; transition: transform 0.2s; }
    .stChatMessage:hover { transform: scale(1.01); border-color: #00d4ff; }
    .st-emotion-cache-pf561s { color: #00d4ff !important; text-shadow: 0 0 10px #00d4ff; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. LOGIC FUNCTIONS ---
def extract_pdf_text(uploaded_file):
    reader = PyPDF2.PdfReader(uploaded_file)
    text = ""
    for page in reader.pages:
        text += page.extract_text()
    return text

if "messages" not in st.session_state: st.session_state.messages = []
if "total_tokens" not in st.session_state: st.session_state.total_tokens = 0

# --- 3. SECURITY & API ---
api_key = st.secrets.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")
if not api_key:
    st.error("Missing API Key. Add it to Secrets!")
    st.stop()
genai.configure(api_key=api_key)

# --- 4. SIDEBAR ---
with st.sidebar:
    st.title("💠 GEM >3 ULTIMATE")
    
    # Feature: Personality Profiles
    persona = st.selectbox("Neural Personality", ["Assistant", "Scientific Analyst", "Creative Storyteller", "Code Architect"])
    sys_prompts = {
        "Assistant": "Helpful AI.",
        "Scientific Analyst": "Focus on data, logic, and peer-reviewed style answers.",
        "Creative Storyteller": "Poetic, descriptive, and imaginative.",
        "Code Architect": "Provide strictly clean code with documentation."
    }

    st.divider()
    # Feature: Multi-format File Upload
    uploaded_file = st.file_uploader("Upload Image or PDF", type=["jpg", "png", "jpeg", "pdf"])
    file_context = ""
    
    if uploaded_file:
        if uploaded_file.type == "application/pdf":
            file_context = extract_pdf_text(uploaded_file)
            st.success("PDF Context Loaded!")
        else:
            st.image(uploaded_file, caption="Image Ready", width='stretch')

    st.divider()
    token_display = st.empty()
    token_display.metric("Total Tokens", f"{st.session_state.total_tokens:,}")
    
    if st.button("🗑️ Reset Neural Link"):
        st.session_state.messages = []
        st.session_state.total_tokens = 0
        st.rerun()

# --- 5. CHAT INTERFACE ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Feature: Voice Input (Native 2026 st.audio_input)
audio_data = st.audio_input("Speak to GEM >3")
text_input = st.chat_input("Command GEM >3...")

# Process Input (Prioritize voice if available)
prompt = text_input
if audio_data and not text_input:
    # Note: In a real app, you'd send this audio to a Whisper/STT API
    prompt = "Analyzing voice command... [User provided audio input]"

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.status("Analyzing and Generating...", expanded=False) as status:
            try:
                # 2026 Model Fallback
                model = genai.GenerativeModel('gemini-2.5-flash', system_instruction=sys_prompts[persona])
                
                # Combine PDF text + Prompt if needed
                full_prompt = f"Context: {file_context}\n\nUser: {prompt}" if file_context else prompt
                
                # Vision handling
                inputs = [full_prompt, Image.open(uploaded_file)] if uploaded_file and uploaded_file.type != "application/pdf" else [full_prompt]
                
                # Streaming Output
                placeholder = st.empty()
                full_response = ""
                response = model.generate_content(inputs, stream=True)
                
                for chunk in response:
                    full_response += chunk.text
                    placeholder.markdown(full_response + "▌")
                
                placeholder.markdown(full_response)
                
                # Usage Telemetry
                st.session_state.total_tokens += response.usage_metadata.total_token_count
                token_display.metric("Total Tokens", f"{st.session_state.total_tokens:,}")
                status.update(label="Sync Complete", state="complete")
                
                st.session_state.messages.append({"role": "assistant", "content": full_response})

            except Exception as e:
                status.update(label="Link Interrupted", state="error")
                st.error(f"Error: {e}")
