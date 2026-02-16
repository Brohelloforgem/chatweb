import streamlit as st
import google.generativeai as genai
from dotenv import load_dotenv
from PIL import Image
import os

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Use the 2026 standard model
model = genai.GenerativeModel('gemini-2.5-flash')

st.set_page_config(page_title="Vision Chatbot", layout="wide")
st.title("GEM <3")

# --- SIDEBAR FOR IMAGES ---
with st.sidebar:
    st.header("Upload Image")
    uploaded_file = st.file_uploader("Choose a photo...", type=["jpg", "jpeg", "png"])
    if uploaded_file:
        img = Image.open(uploaded_file)
        st.image(img, caption="Ready for analysis!", use_container_width=True)

# --- CHAT INTERFACE ---
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Ask about the image or just chat..."):
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Prepare the input (Text + Image if available)
    content_to_send = [prompt]
    if uploaded_file:
        content_to_send.append(img)

    try:
        # Generate response using both text and image
        response = model.generate_content(content_to_send)
        
        with st.chat_message("assistant"):
            st.markdown(response.text)
        
        st.session_state.messages.append({"role": "assistant", "content": response.text})
    except Exception as e:
        st.error(f"Error: {e}")