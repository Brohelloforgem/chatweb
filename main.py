import streamlit as st
from openai import OpenAI
from PIL import Image
import os, base64, requests, json
from io import BytesIO
from dotenv import load_dotenv

# --- 1. CONFIG ---
st.set_page_config(page_title="GEM >3 Ultra-Free", layout="centered")

# --- 2. SESSION INITIALIZATION ---
if "messages" not in st.session_state: st.session_state.messages = []
# We use the official 'openrouter/free' router for high reliability
if "active_model" not in st.session_state: st.session_state.active_model = "openrouter/free"

# --- 3. HELPER FUNCTIONS ---
def encode_image(img):
    img = img.convert("RGB")
    buf = BytesIO()
    img.save(buf, format="JPEG")
    return base64.b64encode(buf.getvalue()).decode('utf-8')

# --- 4. AUTH & CLIENT ---
load_dotenv()
api_key = os.getenv("OPENROUTER_API_KEY") or st.secrets.get("OPENROUTER_API_KEY")
client = OpenAI(
    base_url="https://openrouter.ai/api/v1", 
    api_key=api_key,
    # Adding referer is often required for free models to work correctly
    default_headers={
        "HTTP-Referer": "http://localhost:8501", 
        "X-Title": "GEM-3-Vision"
    }
)

with st.sidebar:
    st.title("🛰️ Smart Routing")
    st.success("Mode: **OpenRouter Free Router**")
    st.caption("Automatically detects Vision/Chat support and avoids limited models.")
    
    st.divider()
    uploaded_file = st.file_uploader("🖼️ Attach Image", type=["jpg", "png", "jpeg"])
    
    if st.button("🗑️ Clear Chat"):
        st.session_state.messages = []
        st.rerun()

# --- 5. CHAT DISPLAY ---
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        if "image_b64" in m:
            st.image(f"data:image/jpeg;base64,{m['image_b64']}", use_container_width=True)
        st.markdown(m["content"])

# --- 6. CHAT INPUT & DYNAMIC ROUTING ---
if prompt := st.chat_input("Message GEM >3..."):
    user_msg = {"role": "user", "content": prompt}
    is_vision = False
    
    if uploaded_file:
        user_msg["image_b64"] = encode_image(Image.open(uploaded_file))
        is_vision = True
    
    st.session_state.messages.append(user_msg)
    
    with st.chat_message("user"):
        if is_vision:
            st.image(f"data:image/jpeg;base64,{user_msg['image_b64']}", use_container_width=True)
        st.markdown(prompt)

    with st.chat_message("assistant"):
        # We use a single, robust API call to 'openrouter/free'
        # It handles fallback, rate limits, and vision-support internally.
        
        api_messages = []
        for m in st.session_state.messages:
            if "image_b64" in m:
                api_messages.append({
                    "role": m["role"],
                    "content": [
                        {"type": "text", "text": m["content"]},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{m['image_b64']}"}}
                    ]
                })
            else:
                api_messages.append({"role": m["role"], "content": m["content"]})

        def stream_gen():
            try:
                # 'openrouter/free' will automatically pick from Gemini, Llama, Qwen, etc.
                response = client.chat.completions.create(
                    model="openrouter/free",
                    messages=api_messages,
                    stream=True
                )
                
                full_text = ""
                for chunk in stream:
                    if chunk.choices and chunk.choices[0].delta.content:
                        content = chunk.choices[0].delta.content
                        full_text += content
                        yield content
                
            except Exception as e:
                yield f"⚠️ **System Alert:** {str(e)}. Try refreshing or wait a minute for the free-tier reset."

        full_res = st.write_stream(stream_gen())
        st.session_state.messages.append({"role": "assistant", "content": full_res})
