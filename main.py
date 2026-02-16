import streamlit as st
from openai import OpenAI
from PIL import Image
import os
import base64
import requests
from io import BytesIO
from dotenv import load_dotenv
import json
import time
import uuid

# ============================================================
# CONFIG
# ============================================================

st.set_page_config(
    page_title="GEM >3 PRO",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# CSS UI
# ============================================================

st.markdown("""
<style>

.main {
    background-color: #0e1117;
    color: #e6edf3;
}

.stChatMessage {
    border-radius: 14px;
    border: 1px solid #30363d;
    background-color: #161b22;
    padding: 10px;
}

.copy-btn {
    float:right;
    font-size:12px;
    padding:4px 8px;
    border-radius:6px;
    border:1px solid #30363d;
    cursor:pointer;
}

.typing {
    opacity:0.6;
    font-style:italic;
}

</style>
""", unsafe_allow_html=True)

# ============================================================
# ENV
# ============================================================

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY") or st.secrets.get("OPENROUTER_API_KEY", "")
APP_PASSWORD = os.getenv("APP_PASSWORD") or st.secrets.get("APP_PASSWORD", "admin")

# ============================================================
# PASSWORD LOGIN
# ============================================================

def check_password():

    if "password_correct" not in st.session_state:
        st.session_state.password_correct = False

    if st.session_state.password_correct:
        return True

    st.title("💠 Secure Neural Login")

    pwd = st.text_input("Access Key", type="password")

    if st.button("Connect"):

        if pwd == APP_PASSWORD:
            st.session_state.password_correct = True
            st.rerun()
        else:
            st.error("Access Denied")

    return False

if not check_password():
    st.stop()

# ============================================================
# OPENROUTER CLIENT
# ============================================================

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY
)

# ============================================================
# SESSION STATE
# ============================================================

if "messages" not in st.session_state:
    st.session_state.messages = []

if "memory" not in st.session_state:
    st.session_state.memory = []

if "uploaded_image" not in st.session_state:
    st.session_state.uploaded_image = None

if "total_tokens" not in st.session_state:
    st.session_state.total_tokens = 0

# ============================================================
# HELPERS
# ============================================================

def encode_image(image):

    buffer = BytesIO()
    image.save(buffer, format="PNG")

    return base64.b64encode(buffer.getvalue()).decode()


@st.cache_data(ttl=3600)
def get_models(api_key):

    try:

        r = requests.get(
            "https://openrouter.ai/api/v1/models",
            headers={"Authorization": f"Bearer {api_key}"}
        )

        data = r.json()["data"]

        models = [m["id"] for m in data]

        free = [m for m in models if ":free" in m]
        paid = [m for m in models if ":free" not in m]

        return free + paid

    except:

        return ["google/gemini-2.0-flash-lite:preview:free"]

# ============================================================
# MEMORY SYSTEM
# ============================================================

def update_memory(user, assistant):

    st.session_state.memory.append({
        "user": user,
        "assistant": assistant
    })

    if len(st.session_state.memory) > 20:
        st.session_state.memory.pop(0)


def build_memory_prompt():

    text = ""

    for m in st.session_state.memory[-10:]:

        text += f"User: {m['user']}\n"
        text += f"Assistant: {m['assistant']}\n"

    return text


# ============================================================
# CHAT EXPORT
# ============================================================

def export_json():

    return json.dumps(st.session_state.messages, indent=2)


def export_txt():

    text = ""

    for m in st.session_state.messages:

        text += f"{m['role']}: {m['content']}\n\n"

    return text


# ============================================================
# COPY BUTTON
# ============================================================

def render_message(content):

    if "```" in content:

        parts = content.split("```")

        for i, part in enumerate(parts):

            if i % 2 == 1:

                code_id = str(uuid.uuid4())

                st.code(part)

                if st.button("Copy", key=code_id):
                    st.toast("Copied")

            else:
                st.markdown(part)

    else:
        st.markdown(content)

# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.title("💠 GEM >3 PRO")

    models = get_models(OPENROUTER_API_KEY)

    selected_model = st.selectbox(
        "Model",
        models
    )

    temperature = st.slider(
        "Creativity",
        0.0,
        1.5,
        0.7
    )

    max_tokens = st.slider(
        "Max Tokens",
        100,
        4000,
        1000
    )

    system_prompt = st.text_area(
        "System Prompt",
        value="You are GEM >3, futuristic AI assistant."
    )

    # IMAGE
    img = st.file_uploader("Image")

    if img:
        st.session_state.uploaded_image = img

    if st.session_state.uploaded_image:
        st.image(st.session_state.uploaded_image)

        if st.button("Clear Image"):
            st.session_state.uploaded_image = None
            st.rerun()

    # EXPORT
    st.download_button(
        "Export JSON",
        export_json(),
        "chat.json"
    )

    st.download_button(
        "Export TXT",
        export_txt(),
        "chat.txt"
    )

    # RESET
    if st.button("Reset Chat"):

        st.session_state.messages = []
        st.session_state.memory = []

        st.rerun()

# ============================================================
# DISPLAY CHAT
# ============================================================

for msg in st.session_state.messages:

    avatar = "🤖" if msg["role"] == "assistant" else "👤"

    with st.chat_message(msg["role"], avatar=avatar):

        render_message(msg["content"])

# ============================================================
# VOICE INPUT
# ============================================================

voice = st.audio_input("Voice Input")

voice_prompt = None

if voice:

    audio_bytes = voice.read()

    with open("voice.wav", "wb") as f:
        f.write(audio_bytes)

    transcript = client.audio.transcriptions.create(
        model="openai/whisper-1",
        file=open("voice.wav", "rb")
    )

    voice_prompt = transcript.text

# ============================================================
# INPUT
# ============================================================

prompt = st.chat_input("Message")

if voice_prompt:
    prompt = voice_prompt

# ============================================================
# GENERATE RESPONSE
# ============================================================

if prompt:

    st.session_state.messages.append({
        "role": "user",
        "content": prompt
    })

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):

        placeholder = st.empty()

        full = ""

        messages = []

        messages.append({
            "role": "system",
            "content": system_prompt + "\nMemory:\n" + build_memory_prompt()
        })

        for m in st.session_state.messages:

            messages.append(m)

        # IMAGE SUPPORT
        if st.session_state.uploaded_image and "gemini" in selected_model.lower():

            img = Image.open(st.session_state.uploaded_image)

            b64 = encode_image(img)

            messages[-1] = {

                "role": "user",

                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{b64}"
                        }
                    }
                ]
            }

        response = client.chat.completions.create(

            model=selected_model,

            messages=messages,

            temperature=temperature,

            max_tokens=max_tokens,

            stream=True
        )

        for chunk in response:

            delta = chunk.choices[0].delta

            if delta and getattr(delta, "content", None):

                full += delta.content

                placeholder.markdown(full + "▌")

                time.sleep(0.01)

        placeholder.markdown(full)

        st.session_state.messages.append({
            "role": "assistant",
            "content": full
        })

        update_memory(prompt, full)
