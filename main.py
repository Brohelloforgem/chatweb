import streamlit as st
import google.generativeai as genai
from PIL import Image
import os
from dotenv import load_dotenv

# --- 1. CONFIGURATION & SECURITY ---
load_dotenv()

# Setup Gemini API (Uses .env locally or Streamlit Secrets in Cloud)
api_key = os.getenv("GEMINI_API_KEY") or st.secrets.get("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)
else:
    st.error("Missing API Key. Please add GEMINI_API_KEY to your secrets.")

# Password Protection Logic
def check_password():
    """Returns True if the user has the correct password."""
    if "password_correct" not in st.session_state:
        st.session_state.password_correct = False

    if st.session_state.password_correct:
        return True

    # Show login form
    st.title("🔐 Secure Chat Access")
    pwd_input = st.text_input("Enter App Password", type="password")
    if st.button("Unlock"):
        # Checks against 'APP_PASSWORD' in your secrets.toml
        if pwd_input == st.secrets["APP_PASSWORD"]:
            st.session_state.password_correct = True
            st.rerun()
        else:
            st.error("🚫 Incorrect password")
    return False

# --- 2. MAIN APP LOGIC ---
if check_password():
    st.set_page_config(page_title="Private Vision AI", layout="wide")
    st.title("🤖 Private Vision Chatbot")
    st.caption("Powered by Gemini 3 Flash | Password Protected")

    # Sidebar for Image Upload
    with st.sidebar:
        st.header("🖼️ Image Analysis")
        uploaded_file = st.file_uploader("Upload an image to discuss", type=["jpg", "jpeg", "png"])
        if uploaded_file:
            st.image(uploaded_file, caption="Target Image", use_container_width=True)

    # Initialize Chat History
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display History
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat Input
    if prompt := st.chat_input("Ask me about the image or just chat..."):
        # Store user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Generate Response
        with st.chat_message("assistant"):
            try:
                # Use Gemini 3 Flash for the best free-tier performance
                model = genai.GenerativeModel('gemini-3-flash')
                
                if uploaded_file:
                    img = Image.open(uploaded_file)
                    response = model.generate_content([prompt, img])
                else:
                    response = model.generate_content(prompt)
                
                full_response = response.text
                st.markdown(full_response)
                st.session_state.messages.append({"role": "assistant", "content": full_response})
            
            except Exception as e:
                st.error(f"Error: {e}")

# --- 3. FOOTER ---
if st.session_state.get("password_correct"):
    if st.button("Logout"):
        st.session_state.password_correct = False
        st.rerun()
