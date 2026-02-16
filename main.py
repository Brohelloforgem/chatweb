import streamlit as st
from openai import OpenAI
from PIL import Image
import os
import json
import base64
from io import BytesIO
from dotenv import load_dotenv

# --- 1. CONFIG & STYLING ---
st.set_page_config(page_title="GEM >3", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stChatMessage { border-radius: 15px; border: 1px solid #30363d; background-color: #161b22; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. SECURITY ---
def check_password():
    if "password_correct" not in st.session_state:
        st.session_state.password_correct = False
    if st.session_state.password_correct: return True

    st.title("💠 OPENROUTER SECURE LINK")
    pwd = st.text_input("Enter Access Key", type="password")
    if st.button("Initialize"):
        if pwd == st.secrets.get("APP_PASSWORD", "admin"):
            st.session_state.password_correct = True
            st.rerun()
        else:
            st.error("Denied.")
    return False

# --- 3. HELPER FUNCTIONS ---
def encode_image(image):
    buffered = BytesIO()
    image.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

if "messages" not in st.session_state: st.session_state.messages = []

if check_password():
    load_dotenv()
    
    # Initialize OpenRouter Client
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.getenv("OPENROUTER_API_KEY") or st.secrets.get("OPENROUTER_API_KEY"),
    )

    with st.sidebar:
        st.title("💠 GEM >3 PRO")
        
        # OpenRouter lets you switch models easily!
        selected_model = st.selectbox("Select Neural Engine", [
            "google/gemini-2.0-flash-lite:free", 
            "google/gemini-2.0-flash",
            "anthropic/claude-3-haiku",
            "meta-llama/llama-3.1-8b-instruct:free"
        ])
        
        sys_prompt = st.text_area("System Instructions", value="You are GEM >3, a witty AI.")
        uploaded_file = st.file_uploader("Visual Input", type=["jpg", "png", "jpeg"])
        
        if st.button("🗑️ Reset Chat"):
            st.session_state.messages = []
            st.rerun()

    # --- 4. CHAT INTERFACE ---
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("Command GEM >3..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.status("Routing through OpenRouter...", expanded=False) as status:
                try:
                    # Prepare messages with system prompt
                    messages = [{"role": "system", "content": sys_prompt}]
                    
                    # Add history
                    for m in st.session_state.messages:
                        messages.append({"role": m["role"], "content": m["content"]})
                    
                    # Handle Vision if image is present (Advanced mode)
                    if uploaded_file and len(st.session_state.messages) == 1:
                        base64_image = encode_image(Image.open(uploaded_file))
                        messages[-1]["content"] = [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_image}"}}
                        ]

                    # Call OpenRouter
                    response = client.chat.completions.create(
                        model=selected_model,
                        messages=messages,
                        stream=True,
                        extra_headers={
                            "HTTP-Referer": "http://localhost:8501", # Optional for rankings
                            "X-Title": "Gemini Streamlit App",
                        }
                    )

                    placeholder = st.empty()
                    full_response = ""
                    for chunk in response:
                        if chunk.choices[0].delta.content:
                            full_response += chunk.choices[0].delta.content
                            placeholder.markdown(full_response + "▌")
                    
                    placeholder.markdown(full_response)
                    st.session_state.messages.append({"role": "assistant", "content": full_response})
                    status.update(label="Transmission Complete", state="complete")

                except Exception as e:
                    st.error(f"API Error: {e}")
                    status.update(label="Error", state="error")
