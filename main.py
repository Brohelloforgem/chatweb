import streamlit as st
from openai import OpenAI
from PIL import Image
import os, base64, requests, json
from io import BytesIO
from dotenv import load_dotenv

# --- 1. CONFIG ---
st.set_page_config(page_title="GEM >3 Pro", layout="centered")

# --- 2. SESSION INITIALIZATION ---
if "messages" not in st.session_state: st.session_state.messages = []
if "total_tokens" not in st.session_state: st.session_state.total_tokens = 0

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
    default_headers={
        "HTTP-Referer": "http://localhost:8501", 
        "X-Title": "GEM-3-Pro"
    }
)

with st.sidebar:
    st.title("GEM >3")
    st.info("Prioritizing: Gemini 2.0 -> Llama 3.2 Vision -> OpenRouter Free")
    
    st.divider()
    uploaded_file = st.file_uploader("🖼️ Attach Image", type=["jpg", "png", "jpeg"])
    
    if st.button("🗑️ Clear Chat"):
        st.session_state.messages = []
        st.session_state.total_tokens = 0
        st.rerun()

# --- 5. CHAT DISPLAY ---
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        if "image_b64" in m:
            st.image(f"data:image/jpeg;base64,{m['image_b64']}", use_container_width=True)
        st.markdown(m["content"])

# --- 6. CHAT INPUT & ROBUST FALLBACK ---
if prompt := st.chat_input("Message GEM >3..."):
    user_msg = {"role": "user", "content": prompt}
    if uploaded_file:
        user_msg["image_b64"] = encode_image(Image.open(uploaded_file))
    
    st.session_state.messages.append(user_msg)
    
    with st.chat_message("user"):
        if "image_b64" in user_msg:
            st.image(f"data:image/jpeg;base64,{user_msg['image_b64']}", use_container_width=True)
        st.markdown(prompt)

    with st.chat_message("assistant"):
        # Format the history correctly for Multimodal LLMs
        api_messages = [{"role": "system", "content": "You are a professional AI with vision."}]
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

        # Manual Fallback Logic: Try these models in order
        models_to_try = [
            "google/gemini-2.0-flash-lite:preview:free", 
            "meta-llama/llama-3.2-11b-vision-instruct:free",
            "openrouter/free" 
        ]

        def stream_gen():
            last_error = ""
            for model_id in models_to_try:
                try:
                    # Logic fix: renamed stream variable correctly
                    response_stream = client.chat.completions.create(
                        model=model_id,
                        messages=api_messages,
                        stream=True,
                    )
                    
                    full_text = ""
                    for chunk in response_stream:
                        if chunk.choices and chunk.choices[0].delta.content:
                            content = chunk.choices[0].delta.content
                            full_text += content
                            yield content
                    
                    # If we got here, it worked! Exit the model loop.
                    return 

                except Exception as e:
                    last_error = str(e)
                    continue # Try the next model
            
            yield f"⚠️ **All neural links saturated.** Last error: {last_error}"

        full_res = st.write_stream(stream_gen())
        st.session_state.messages.append({"role": "assistant", "content": full_res})
