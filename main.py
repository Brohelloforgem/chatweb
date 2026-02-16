import streamlit as st
from openai import OpenAI
from PIL import Image
import os
import json
import base64
import requests
from io import BytesIO
from dotenv import load_dotenv

# --- 1. CONFIG & STYLING ---
st.set_page_config(page_title="GEM >3 (OpenRouter)", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    .main { background-color: #0e1117; color: #e6edf3; }
    .stChatMessage { border-radius: 15px; border: 1px solid #30363d; background-color: #161b22; margin-bottom: 10px; }
    .stChatInput { border-color: #30363d !important; }
    .st-emotion-cache-pf561s { color: #00d4ff !important; text-shadow: 0 0 10px #00d4ff; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. SECURITY ---
def check_password():
    if "password_correct" not in st.session_state:
        st.session_state.password_correct = False
    if st.session_state.password_correct: return True

    st.title("💠 NEURAL LINK SECURE LOGIN")
    pwd = st.text_input("Access Key", type="password")
    if st.button("Initialize Neural Link"):
        if pwd == st.secrets.get("APP_PASSWORD", "admin"):
            st.session_state.password_correct = True
            st.rerun()
        else:
            st.error("Access Denied.")
    return False

# --- 3. HELPER FUNCTIONS ---
def encode_image(image):
    buffered = BytesIO()
    image.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

@st.cache_data(ttl=3600)  # Refresh model list every hour
def get_openrouter_models(api_key):
    try:
        response = requests.get(
            "https://openrouter.ai/api/v1/models",
            headers={"Authorization": f"Bearer {api_key}"}
        )
        if response.status_code == 200:
            data = response.json().get('data', [])
            # Filter for models that are either free or commonly used
            return [m['id'] for m in data]
        return ["google/gemini-2.0-flash-lite:preview:free", "meta-llama/llama-3.1-8b-instruct:free"]
    except:
        return ["google/gemini-2.0-flash-lite:preview:free"]

# --- 4. SESSION INITIALIZATION ---
if "messages" not in st.session_state: st.session_state.messages = []
if "total_tokens" not in st.session_state: st.session_state.total_tokens = 0

if check_password():
    load_dotenv()
    OR_API_KEY = os.getenv("OPENROUTER_API_KEY") or st.secrets.get("OPENROUTER_API_KEY")
    
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=OR_API_KEY,
    )

    # --- SIDEBAR ---
    with st.sidebar:
        st.title("💠 GEM >3 PRO")
        
        st.subheader("⚙️ Engine Configuration")
        available_models = get_openrouter_models(OR_API_KEY)
        
        # Priority Free models first for easier selection
        default_models = [m for m in available_models if ":free" in m] + [m for m in available_models if ":free" not in m]
        
        selected_model = st.selectbox("Neural Engine", default_models, index=0)
        
        sys_prompt = st.text_area("System Instructions", 
            value="You are GEM >3, a futuristic AI. Be helpful, concise, and slightly witty.",
            help="Define the bot's personality.")
        
        st.divider()
        uploaded_file = st.file_uploader("Visual Input", type=["jpg", "png", "jpeg"])
        if uploaded_file: st.image(uploaded_file, use_container_width=True)
        
        st.divider()
        st.metric("Session Activity", f"{len(st.session_state.messages)} messages")
        
        if st.button("🗑️ Reset Link"):
            st.session_state.messages = []
            st.rerun()

    # --- 5. CHAT INTERFACE ---
    # Display message history
    for msg in st.session_state.messages:
        role = "assistant" if msg["role"] == "assistant" else "user"
        avatar = "🤖" if role == "assistant" else "👤"
        with st.chat_message(role, avatar=avatar):
            st.markdown(msg["content"])

    # Chat Input
    if prompt := st.chat_input("Command GEM >3..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user", avatar="👤"):
            st.markdown(prompt)

        with st.chat_message("assistant", avatar="🤖"):
            with st.status("Routing through OpenRouter...", expanded=False) as status:
                try:
                    # Construct Message Payload
                    chat_history = [{"role": "system", "content": sys_prompt}]
                    for m in st.session_state.messages:
                        chat_history.append({"role": m["role"], "content": m["content"]})
                    
                    # Handle Image Attachment (Only for the latest message if image exists)
                    if uploaded_file:
                        base64_image = encode_image(Image.open(uploaded_file))
                        # Transform the last user message into a multimodal format
                        chat_history[-1]["content"] = [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_image}"}}
                        ]

                    # API Call
                    response = client.chat.completions.create(
                        model=selected_model,
                        messages=chat_history,
                        stream=True,
                        extra_headers={
                            "HTTP-Referer": "http://localhost:8501", 
                            "X-Title": "GEM-3-Pro-Streamlit",
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
                    status.update(label="Transmission Successful", state="complete")

                except Exception as e:
                    status.update(label="Routing Error", state="error")
                    st.error(f"Error: {str(e)}")
