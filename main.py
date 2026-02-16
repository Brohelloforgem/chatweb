import streamlit as st
import google.generativeai as genai
from PIL import Image
import os
from dotenv import load_dotenv

load_dotenv()

# --- SECURITY CHECK ---
def check_password():
    if "password_correct" not in st.session_state:
        st.session_state.password_correct = False
    if st.session_state.password_correct:
        return True

    st.title("🔐 Secure Chat Access")
    pwd_input = st.text_input("Enter App Password", type="password")
    if st.button("Unlock"):
        # Accessing secrets safely
        if pwd_input == st.secrets.get("APP_PASSWORD", "admin"):
            st.session_state.password_correct = True
            st.rerun()
        else:
            st.error("🚫 Incorrect password")
    return False

if check_password():
    # Set config FIRST
    st.set_page_config(page_title="AI Vision + Token Tracker", layout="wide")
    
    # Configure API
    api_key = os.getenv("GEMINI_API_KEY") or st.secrets.get("GEMINI_API_KEY")
    genai.configure(api_key=api_key)

    # Sidebar
    with st.sidebar:
        st.header("⚙️ Controls")
        uploaded_file = st.file_uploader("Upload an image", type=["jpg", "jpeg", "png"])
        if uploaded_file:
            # FIX: Updated width parameter for 2026 Streamlit standards
            st.image(uploaded_file, width='stretch') 
        
        st.divider()
        st.subheader("📊 Token Usage")
        token_container = st.container()

    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "total_tokens" not in st.session_state:
        st.session_state.total_tokens = 0

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Ask me something..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            # FIX: Using the widely supported stable model name
            model = genai.GenerativeModel('gemini-1.5-flash') 
            
            content = [prompt, Image.open(uploaded_file)] if uploaded_file else [prompt]
            
            try:
                response = model.generate_content(content)
                ans = response.text
                usage = response.usage_metadata
                
                st.markdown(ans)
                st.session_state.messages.append({"role": "assistant", "content": ans})
                st.session_state.total_tokens += usage.total_token_count

                # Update sidebar stats
                with token_container:
                    st.write(f"**Last Prompt:** {usage.prompt_token_count}")
                    st.write(f"**Last Response:** {usage.candidates_token_count}")
                    st.metric("Total Tokens Used", f"{st.session_state.total_tokens:,}")
            
            except Exception as e:
                st.error(f"API Error: {e}")
