import streamlit as st
from openai import OpenAI
from PIL import Image
import os, base64, requests, json
from io import BytesIO
from dotenv import load_dotenv

# --- 1. CONFIG ---
st.set_page_config(page_title="GEM >3 Ultimate", layout="centered")

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
    default_headers={"HTTP-Referer": "http://localhost:8501", "X-Title": "GEM-3-Ultimate"}
)

with st.sidebar:
    st.title("🛰️ Neural Link")
    # Updated the info to reflect the 3-model limit
    st.info("⚡ Fallback: Gemma 3 → Llama 3.2 → Free Router")
    uploaded_file = st.file_uploader("🖼️ Attach Image", type=["jpg", "png", "jpeg"])
    if st.button("🗑️ Clear Chat"):
        st.session_state.messages = []; st.session_state.total_tokens = 0; st.rerun()

# --- 5. CHAT DISPLAY ---
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        if "image_b64" in m:
            st.image(f"data:image/jpeg;base64,{m['image_b64']}", use_container_width=True)
        st.markdown(m["content"])

# --- 6. SMART INPUT & SYSTEM ROLE INJECTION ---
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
        sys_instr = "You are GEM >3, a professional AI. Use vision to analyze images accurately."
        api_messages = []
        
        # FIX: System instructions injected into the first user message (avoiding 400 errors)
        for i, m in enumerate(st.session_state.messages):
            content_to_send = m["content"]
            if i == 0 and m["role"] == "user":
                content_to_send = f"SYSTEM INSTRUCTIONS: {sys_instr}\n\nUSER PROMPT: {m['content']}"

            if "image_b64" in m:
                api_messages.append({
                    "role": m["role"],
                    "content": [
                        {"type": "text", "text": content_to_send},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{m['image_b64']}"}}
                    ]
                })
            else:
                api_messages.append({"role": m["role"], "content": content_to_send})

        # CRITICAL FIX: The list below MUST NOT exceed 3 items
        models_to_try = [
            "google/gemini-2.0-flash-lite:preview:free", # Primary (Vision powerhouse)
            "meta-llama/llama-3.2-11b-vision-instruct:free", # Secondary
            "openrouter/free" # Ultimate catch-all
        ]

        def stream_gen():
            last_err = ""
            # We try the primary first, and if it fails, the 'extra_body' handles the next 2
            try:
                response_stream = client.chat.completions.create(
                    model=models_to_try[0],
                    messages=api_messages,
                    stream=True,
                    # Fallback happens on the server side for the remaining 2 models
                    extra_body={"models": models_to_try[1:]} 
                )
                
                for chunk in response_stream:
                    if chunk.choices and chunk.choices[0].delta.content:
                        yield chunk.choices[0].delta.content
                return 

            except Exception as e:
                last_err = str(e)
            
            yield f"⚠️ **Neural Link Failed.** {last_err}"

        full_res = st.write_stream(stream_gen())
        st.session_state.messages.append({"role": "assistant", "content": full_res})
