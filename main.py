import streamlit as st
from openai import OpenAI
from PIL import Image
import os, base64, requests, json
from io import BytesIO
from datetime import datetime
from dotenv import load_dotenv

# --- 1. CONFIG ---
st.set_page_config(page_title="GEM >3 Vision", layout="centered")

st.markdown("""
    <style>
    .stMainBlockContainer { max-width: 800px; padding-top: 2rem; }
    /* Ensure images in chat don't take up too much vertical space */
    .stChatFloatingInputContainer { background-color: rgba(0,0,0,0); }
    </style>
    """, unsafe_allow_html=True)

# --- 2. SESSION INITIALIZATION ---
if "messages" not in st.session_state: st.session_state.messages = []
if "total_tokens" not in st.session_state: st.session_state.total_tokens = 0

# --- 3. HELPER FUNCTIONS ---
def encode_image(img):
    """Convert PIL image to base64 string for API and display."""
    buf = BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode('utf-8')

@st.cache_data(ttl=3600)
def get_engines(api_key):
    try:
        r = requests.get("https://openrouter.ai/api/v1/models", headers={"Authorization": f"Bearer {api_key}"})
        return [m['id'] for m in r.json().get('data', [])]
    except: return ["google/gemini-2.0-flash-lite:preview:free"]

# --- 4. MAIN INTERFACE ---
load_dotenv()
api_key = os.getenv("OPENROUTER_API_KEY") or st.secrets.get("OPENROUTER_API_KEY")
client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=api_key)

with st.sidebar:
    st.title("⚙️ Control Panel")
    engines = get_engines(api_key)
    selected_model = st.selectbox("Intelligence Core", engines, index=0)
    
    st.divider()
    # Feature: Dedicated image uploader
    uploaded_file = st.file_uploader("🖼️ Attach Image to Next Message", type=["jpg", "png", "jpeg"])
    
    st.divider()
    st.metric("Session Tokens", f"{st.session_state.total_tokens:,}")
    if st.button("🗑️ Clear Chat"):
        st.session_state.messages = []
        st.session_state.total_tokens = 0
        st.rerun()

# --- 5. CHAT HISTORY DISPLAY ---
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        # If the message has an image, display it first
        if "image_b64" in m:
            st.image(f"data:image/png;base64,{m['image_b64']}", use_container_width=True)
        st.markdown(m["content"])

# --- 6. CHAT INPUT & VISION LOGIC ---
if prompt := st.chat_input("Message GEM >3..."):
    # Create the message object
    new_message = {"role": "user", "content": prompt}
    
    # If an image was uploaded, attach it to this specific message
    image_b64 = None
    if uploaded_file:
        img = Image.open(uploaded_file)
        image_b64 = encode_image(img)
        new_message["image_b64"] = image_b64

    st.session_state.messages.append(new_message)
    
    # Display the user's message immediately
    with st.chat_message("user"):
        if image_b64:
            st.image(f"data:image/png;base64,{image_b64}", use_container_width=True)
        st.markdown(prompt)

    # Generate Assistant Response
    with st.chat_message("assistant"):
        # Prepare history for the API
        api_history = [{"role": "system", "content": "You are a helpful AI that can see images."}]
        
        for m in st.session_state.messages:
            if "image_b64" in m:
                # OpenRouter Multimodal format
                api_history.append({
                    "role": m["role"],
                    "content": [
                        {"type": "text", "text": m["content"]},
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{m['image_b64']}"}}
                    ]
                })
            else:
                api_history.append({"role": m["role"], "content": m["content"]})

        # Stream the response
        def stream_gen():
            stream = client.chat.completions.create(
                model=selected_model,
                messages=api_history,
                stream=True,
                stream_options={"include_usage": True}
            )
            for chunk in stream:
                if hasattr(chunk, 'usage') and chunk.usage:
                    st.session_state.total_tokens += chunk.usage.total_tokens
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        full_res = st.write_stream(stream_gen())
        st.session_state.messages.append({"role": "assistant", "content": full_res})
        st.rerun()
