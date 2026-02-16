import streamlit as st
from openai import OpenAI
from PIL import Image
import os, base64, requests, json
from io import BytesIO
from datetime import datetime
from dotenv import load_dotenv

# --- 1. CONFIG ---
st.set_page_config(page_title="GEM >3 Vision", layout="centered")

# --- 2. SESSION INITIALIZATION ---
if "messages" not in st.session_state: st.session_state.messages = []
if "total_tokens" not in st.session_state: st.session_state.total_tokens = 0

# --- 3. HELPER FUNCTIONS ---
def encode_image(img):
    """Standardize image to RGB and convert to base64."""
    img = img.convert("RGB")
    buf = BytesIO()
    img.save(buf, format="JPEG")
    return base64.b64encode(buf.getvalue()).decode('utf-8')

@st.cache_data(ttl=3600)
def get_engines(api_key):
    try:
        r = requests.get("https://openrouter.ai/api/v1/models", headers={"Authorization": f"Bearer {api_key}"})
        return [m['id'] for m in r.json().get('data', [])]
    except: return ["google/gemini-2.0-flash-lite:preview:free"]

# --- 4. AUTH & CLIENT ---
load_dotenv()
api_key = os.getenv("OPENROUTER_API_KEY") or st.secrets.get("OPENROUTER_API_KEY")
client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=api_key)

with st.sidebar:
    st.title("⚙️ Control Panel")
    engines = get_engines(api_key)
    selected_model = st.selectbox("Intelligence Core", engines, index=0)
    
    st.divider()
    # Image uploader stays in sidebar for a cleaner UI
    uploaded_file = st.file_uploader("🖼️ Attach Image", type=["jpg", "png", "jpeg"])
    
    st.divider()
    st.metric("Session Tokens", f"{st.session_state.total_tokens:,}")
    if st.button("🗑️ Clear Chat"):
        st.session_state.messages = []
        st.session_state.total_tokens = 0
        st.rerun()

# --- 5. CHAT HISTORY DISPLAY ---
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        if "image_b64" in m:
            st.image(f"data:image/jpeg;base64,{m['image_b64']}", use_container_width=True)
        st.markdown(m["content"])

# --- 6. CHAT INPUT & VISION LOGIC ---
if prompt := st.chat_input("Message GEM >3..."):
    # Store user message with image if present
    user_msg = {"role": "user", "content": prompt}
    if uploaded_file:
        user_msg["image_b64"] = encode_image(Image.open(uploaded_file))
    
    st.session_state.messages.append(user_msg)
    
    # Render user message
    with st.chat_message("user"):
        if "image_b64" in user_msg:
            st.image(f"data:image/jpeg;base64,{user_msg['image_b64']}", use_container_width=True)
        st.markdown(prompt)

    # Render assistant response
    with st.chat_message("assistant"):
        # BUILD PROPER MULTIMODAL HISTORY
        api_messages = [{"role": "system", "content": "You are a helpful AI with vision capabilities."}]
        
        for m in st.session_state.messages:
            if "image_b64" in m:
                # This is the "Multi-part" format required for vision
                api_messages.append({
                    "role": m["role"],
                    "content": [
                        {"type": "text", "text": m["content"]},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{m['image_b64']}"}}
                    ]
                })
            else:
                api_messages.append({"role": m["role"], "content": m["content"]})

        # STREAMING GENERATOR
        def stream_gen():
            try:
                stream = client.chat.completions.create(
                    model=selected_model,
                    messages=api_messages,
                    stream=True,
                    stream_options={"include_usage": True}
                )
                for chunk in stream:
                    # Update token count from usage chunk if available
                    if hasattr(chunk, 'usage') and chunk.usage:
                        st.session_state.total_tokens += chunk.usage.total_tokens
                    # Yield text content
                    if chunk.choices and chunk.choices[0].delta.content:
                        yield chunk.choices[0].delta.content
            except Exception as e:
                yield f"⚠️ API Error: {str(e)}"

        full_res = st.write_stream(stream_gen())
        st.session_state.messages.append({"role": "assistant", "content": full_res})
        
        # Trigger one final rerun to update the sidebar token metric
        st.rerun()
