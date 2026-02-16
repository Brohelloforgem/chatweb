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
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="GEM >3 PRO (FREE)",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# CSS
# ============================================================

st.markdown("""
<style>

.main {
    background-color: #0e1117;
    color: #e6edf3;
}

.stChatMessage {
    border-radius: 12px;
    border: 1px solid #30363d;
    background-color: #161b22;
    padding: 10px;
}

</style>
""", unsafe_allow_html=True)

# ============================================================
# LOAD ENV
# ============================================================

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY") or st.secrets.get("OPENROUTER_API_KEY", "")
APP_PASSWORD = os.getenv("APP_PASSWORD") or st.secrets.get("APP_PASSWORD", "admin")

# ============================================================
# PASSWORD
# ============================================================

def check_password():

    if "password_correct" not in st.session_state:
        st.session_state.password_correct = False

    if st.session_state.password_correct:
        return True

    st.title("🔐 GEM >3 Secure Access")

    pwd = st.text_input("Password", type="password")

    if st.button("Login"):

        if pwd == APP_PASSWORD:
            st.session_state.password_correct = True
            st.rerun()

        else:
            st.error("Incorrect password")

    return False


if not check_password():
    st.stop()

# ============================================================
# CLIENT
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

# ============================================================
# FETCH FREE MODELS ONLY
# ============================================================

@st.cache_data(ttl=3600)
def get_free_models(api_key):

    try:

        r = requests.get(
            "https://openrouter.ai/api/v1/models",
            headers={"Authorization": f"Bearer {api_key}"}
        )

        data = r.json()["data"]

        free = [
            m["id"]
            for m in data
            if ":free" in m["id"]
        ]

        free.sort()

        return free

    except:

        return [
            "google/gemini-2.0-flash-lite:preview:free",
            "deepseek/deepseek-chat:free",
            "meta-llama/llama-3.1-8b-instruct:free"
        ]

# ============================================================
# HELPERS
# ============================================================

def encode_image(image):

    buffer = BytesIO()
    image.save(buffer, format="PNG")

    return base64.b64encode(buffer.getvalue()).decode()


def build_memory():

    text = ""

    for m in st.session_state.memory[-10:]:

        text += f"User: {m['user']}\n"
        text += f"Assistant: {m['assistant']}\n"

    return text


def update_memory(user, assistant):

    st.session_state.memory.append({
        "user": user,
        "assistant": assistant
    })

    if len(st.session_state.memory) > 20:
        st.session_state.memory.pop(0)


def export_json():

    return json.dumps(st.session_state.messages, indent=2)


def export_txt():

    text = ""

    for m in st.session_state.messages:
        text += f"{m['role']}: {m['content']}\n\n"

    return text


def render_message(content):

    if "```" in content:

        parts = content.split("```")

        for i, part in enumerate(parts):

            if i % 2 == 1:

                st.code(part)

                if st.button("Copy", key=str(uuid.uuid4())):
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

    free_models = get_free_models(OPENROUTER_API_KEY)

    selected_model = st.selectbox(
        "Free Model",
        free_models
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

    img = st.file_uploader("Upload Image")

    if img:
        st.session_state.uploaded_image = img

    if st.session_state.uploaded_image:

        st.image(st.session_state.uploaded_image)

        if st.button("Clear Image"):

            st.session_state.uploaded_image = None
            st.rerun()

    st.download_button("Export JSON", export_json(), "chat.json")
    st.download_button("Export TXT", export_txt(), "chat.txt")

    if st.button("Reset Chat"):

        st.session_state.messages = []
        st.session_state.memory = []

        st.rerun()

# ============================================================
# AUTO SWITCH TO GEMINI IF IMAGE
# ============================================================

if st.session_state.uploaded_image:

    gemini_models = [
        m for m in free_models
        if "gemini" in m.lower()
    ]

    if gemini_models and "gemini" not in selected_model.lower():

        selected_model = gemini_models[0]

        st.sidebar.success(f"Vision enabled: {selected_model}")

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

voice_prompt = None

audio = st.audio_input("Voice Input")

if audio:

    with open("voice.wav", "wb") as f:
        f.write(audio.read())

    transcript = client.audio.transcriptions.create(
        model="whisper-1",
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
# RESPONSE
# ============================================================

if prompt:

    if ":free" not in selected_model:

        st.error("Only free models allowed")
        st.stop()

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
            "content": system_prompt + "\nMemory:\n" + build_memory()
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

        try:

            response = client.chat.completions.create(

                model=selected_model,

                messages=messages,

                temperature=temperature,

                max_tokens=max_tokens,

                stream=True,

                extra_headers={
                    "HTTP-Referer": "https://your-app.streamlit.app",
                    "X-Title": "GEM-3-PRO"
                }
            )

            for chunk in response:

                delta = chunk.choices[0].delta

                if delta and getattr(delta, "content", None):

                    full += delta.content

                    placeholder.markdown(full + "▌")

                    time.sleep(0.01)

            placeholder.markdown(full)

        except Exception as e:

            st.error(str(e))
            st.stop()

        st.session_state.messages.append({
            "role": "assistant",
            "content": full
        })

        update_memory(prompt, full)
