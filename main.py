import streamlit as st
from openai import OpenAI
from PIL import Image
import os, base64, requests, json
from io import BytesIO
from dotenv import load_dotenv

# --- 1. COMMAND CENTER CONFIG ---
st.set_page_config(page_title="GEM >3 ULTRA", layout="wide", initial_sidebar_state="expanded")

# Ultra-Modern CSS Injection
st.markdown("""
    <style>
    /* Global Background & Glassmorphism */
    .stApp { background: linear-gradient(160deg, #020617 0%, #0f172a 100%); color: #f8fafc; }
    
    /* Custom Sticky Header */
    [data-testid="stHeader"] { background: rgba(15, 23, 42, 0.7); backdrop-filter: blur(15px); border-bottom: 1px solid #1e293b; }

    /* Neon Chat Bubbles */
    .stChatMessage {
        background-color: #1e293b !important;
        border: 1px solid #334155 !important;
        border-radius: 18px !important;
        padding: 1.2rem !important;
        margin-bottom: 1rem !important;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.2);
    }
    
    /* Distinct Assistant Glow */
    .stChatMessage:has([data-testid="stChatMessageAvatarAssistant"]) {
        border-left: 4px solid #3b82f6 !important;
        background: linear-gradient(90deg, #1e293b 0%, #0f172a 100%) !important;
    }

    /* Sidebar Refinement */
    section[data-testid="stSidebar"] { background-color: #020617 !important; border-right: 1px solid #1e293b; }
    
    /* Input Field Aesthetic */
    .stChatInputContainer > div { 
        background-color: #1e293b !important; 
        border: 1px solid #3b82f6 !important; 
        border-radius: 14px !important;
        padding: 5px !important;
    }

    /* Scrollbar Styling */
    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-thumb { background: #3b82f6; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. AUTH & DYNAMIC ENGINE FETCH ---
def check_password():
    if "password_correct" not in st.session_state: st.session_state.password_correct = False
    if st.session_state.password_correct: return True
    
    st.title("💠 NEURAL LINK SECURE GATE")
    pwd = st.text_input("Access Key", type="password")
    if st.button("Initialize Neural Link"):
        if pwd == st.secrets.get("APP_PASSWORD", "admin"):
            st.session_state.password_correct = True
            st.rerun()
    return False

@st.cache_data(ttl=3600)
def get_live_engines(api_key):
    try:
        r = requests.get("https://openrouter.ai/api/v1/models", headers={"Authorization": f"Bearer {api_key}"})
        # Filter for models with 'free' in ID to prioritize zero-cost endpoints
        models = [m['id'] for m in r.json().get('data', [])]
        free_models = [m for m in models if ":free" in m]
        return free_models + [m for m in models if ":free" not in m]
    except: return ["google/gemini-2.0-flash-lite:preview:free"]

def encode_image(img):
    buf = BytesIO(); img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode('utf-8')

# --- 3. APP ENGINE ---
if check_password():
    load_dotenv()
    api_key = os.getenv("OPENROUTER_API_KEY") or st.secrets.get("OPENROUTER_API_KEY")
    client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=api_key)

    if "messages" not in st.session_state: st.session_state.messages = []

    with st.sidebar:
        st.markdown("<h2 style='color:#3b82f6;'>💠 SYSTEM SETTINGS</h2>", unsafe_allow_html=True)
        engines = get_live_engines(api_key)
        selected_model = st.selectbox("Intelligence Core", engines)
        
        sys_prompt = st.text_area("System Directive", "You are GEM >3, an advanced AI. Concise and witty.")
        
        st.divider()
        uploaded_file = st.file_uploader("Visual Feed", type=["jpg", "png", "jpeg"])
        if uploaded_file: st.image(uploaded_file, caption="Vision Feed Active", use_container_width=True)
        
        if st.button("🗑️ Purge Neural Cache"):
            st.session_state.messages = []; st.rerun()

    # --- 4. NEURAL INTERFACE ---
    st.markdown(f"### 💬 Active Link: `{selected_model.split('/')[-1]}`")
    
    for m in st.session_state.messages:
        avatar = "🤖" if m["role"] == "assistant" else "👤"
        with st.chat_message(m["role"], avatar=avatar):
            st.markdown(m["content"])

    if prompt := st.chat_input("Input command for GEM >3..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user", avatar="👤"):
            st.markdown(prompt)

        with st.chat_message("assistant", avatar="🤖"):
            with st.status("Synthesizing response...", expanded=False) as status:
                try:
                    history = [{"role": "system", "content": sys_prompt}]
                    # Pass the last 10 messages for context (Memory management)
                    for m in st.session_state.messages[-10:]: history.append(m)
                    
                    if uploaded_file:
                        b64 = encode_image(Image.open(uploaded_file))
                        history[-1]["content"] = [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}}
                        ]
                    
                    stream = client.chat.completions.create(model=selected_model, messages=history, stream=True)
                    
                    full_res = ""; holder = st.empty()
                    for chunk in stream:
                        if chunk.choices[0].delta.content:
                            full_res += chunk.choices[0].delta.content
                            holder.markdown(full_res + "┃")
                    
                    holder.markdown(full_res)
                    st.session_state.messages.append({"role": "assistant", "content": full_res})
                    status.update(label="Response Synthesized", state="complete")
                    
                except Exception as e:
                    status.update(label="Neural Link Error", state="error")
                    st.error(f"Transmission Failed: {e}")
