# main.py
import streamlit as st
from openai import OpenAI
from PIL import Image
import os
import base64
import requests
from io import BytesIO
from dotenv import load_dotenv

# ============================================================
# 1. PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="GEM >3 PRO",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# 2. CUSTOM CSS (ChatGPT-style Dark UI)
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
    padding: 12px;
}

.stChatInput textarea {
    background-color: #161b22 !important;
    color: white !important;
}

.sidebar .sidebar-content {
    background-color: #0e1117;
}

.glow {
    color: #00d4ff;
    text-shadow: 0 0 10px #00d4ff;
}

</style>
""", unsafe_allow_html=True)


# ============================================================
# 3. LOAD ENV
# ============================================================

load_dotenv()

OR_API_KEY = os.getenv("OPENROUTER_API_KEY") or st.secrets.get("OPENROUTER_API_KEY", "")
APP_PASSWORD = os.getenv("APP_PASSWORD") or st.secrets.get("APP_PASSWORD", "admin")

# ============================================================
# 4. PASSWORD PROTECTION
# ============================================================

def check_password():

    if "password_correct" not in st.session_state:
        st.session_state.password_correct = False

    if st.session_state.password_correct:
        return True

    st.title("💠 NEURAL LINK SECURE LOGIN")

    password = st.text_input("Access Key", type="password")

    if st.button("Initialize Neural Link"):

        if password == APP_PASSWORD:
            st.session_state.password_correct = True
            st.rerun()

        else:
            st.error("Access Denied")

    return False


# ============================================================
# 5. OPENROUTER CLIENT
# ============================================================

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OR_API_KEY
)

# ============================================================
# 6. SESSION STATE INIT
# ============================================================

if "messages" not in st.session_state:
    st.session_state.messages = []

if "uploaded_image" not in st.session_state:
    st.session_state.uploaded_image = None

if "total_tokens" not in st.session_state:
    st.session_state.total_tokens = 0


# ============================================================
# 7. HELPERS
# ============================================================

def encode_image(image):

    buffered = BytesIO()

    image.save(buffered, format="PNG")

    return base64.b64encode(buffered.getvalue()).decode()


@st.cache_data(ttl=3600)
def get_models(api_key):

    try:

        response = requests.get(
            "https://openrouter.ai/api/v1/models",
            headers={"Authorization": f"Bearer {api_key}"}
        )

        data = response.json()["data"]

        models = [m["id"] for m in data]

        free = [m for m in models if ":free" in m]
        paid = [m for m in models if ":free" not in m]

        return free + paid

    except:

        return [
            "google/gemini-2.0-flash-lite:preview:free",
            "meta-llama/llama-3.1-8b-instruct:free"
        ]


# ============================================================
# 8. MAIN APP
# ============================================================

if not check_password():
    st.stop()

# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.title("💠 GEM >3 PRO")

    models = get_models(OR_API_KEY)

    selected_model = st.selectbox(
        "Neural Engine",
        models,
        index=0
    )

    system_prompt = st.text_area(
        "System Instructions",
        value="You are GEM >3, a futuristic AI. Be helpful, concise, and slightly witty."
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

    st.divider()

    uploaded_file = st.file_uploader(
        "Visual Input",
        type=["png", "jpg", "jpeg"]
    )

    if uploaded_file:
        st.session_state.uploaded_image = uploaded_file

    if st.session_state.uploaded_image:

        st.image(
            st.session_state.uploaded_image,
            use_container_width=True
        )

        if st.button("Clear Image"):
            st.session_state.uploaded_image = None
            st.rerun()

    st.divider()

    st.metric("Messages", len(st.session_state.messages))

    st.metric("Tokens Used", st.session_state.total_tokens)

    if st.button("Reset Chat"):

        st.session_state.messages = []

        st.session_state.total_tokens = 0

        st.rerun()


# ============================================================
# DISPLAY CHAT HISTORY
# ============================================================

for message in st.session_state.messages:

    role = message["role"]

    avatar = "🤖" if role == "assistant" else "👤"

    with st.chat_message(role, avatar=avatar):

        st.markdown(message["content"])


# ============================================================
# CHAT INPUT
# ============================================================

prompt = st.chat_input("Command GEM >3...")

if prompt:

    st.session_state.messages.append(
        {"role": "user", "content": prompt}
    )

    with st.chat_message("user", avatar="👤"):

        st.markdown(prompt)


    with st.chat_message("assistant", avatar="🤖"):

        placeholder = st.empty()

        full_response = ""

        try:

            chat_messages = [

                {"role": "system", "content": system_prompt}

            ]

            # Add history
            for m in st.session_state.messages:

                chat_messages.append(
                    {
                        "role": m["role"],
                        "content": m["content"]
                    }
                )

            # Add image if exists
            if st.session_state.uploaded_image:

                img = Image.open(st.session_state.uploaded_image)

                base64_img = encode_image(img)

                chat_messages[-1] = {

                    "role": "user",

                    "content": [

                        {"type": "text", "text": prompt},

                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{base64_img}"
                            }
                        }

                    ]
                }

            # STREAM RESPONSE
            response = client.chat.completions.create(

                model=selected_model,

                messages=chat_messages,

                temperature=temperature,

                max_tokens=max_tokens,

                stream=True,

                extra_headers={

                    "HTTP-Referer": "http://localhost:8501",

                    "X-Title": "GEM-3-Pro"

                }

            )

            for chunk in response:

                delta = chunk.choices[0].delta

                if delta and getattr(delta, "content", None):

                    full_response += delta.content

                    placeholder.markdown(full_response + "▌")

            placeholder.markdown(full_response)

            st.session_state.messages.append(
                {"role": "assistant", "content": full_response}
            )

        except Exception as e:

            st.error(f"Error: {str(e)}")
