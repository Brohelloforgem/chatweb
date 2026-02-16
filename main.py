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
    st.title("GEM >3")
    st.caption("Powered by Gemini 2.5 Flash | Password Protected")
    
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
                model = genai.GenerativeModel('gemini-2.5-flash')
                
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
# Sidebar for Uploads and Token Stats
    with st.sidebar:
        st.header("⚙️ Controls")
        uploaded_file = st.file_uploader("Upload an image", type=["jpg", "jpeg", "png"])
        if uploaded_file:
            st.image(uploaded_file, use_container_width=True)
        
        st.divider()
        st.subheader("📊 Token Usage")
        # Placeholder for usage stats
        token_container = st.container()

    # Chat logic
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
            model = genai.GenerativeModel('gemini-3-flash')
            
            # Send prompt (and image if exists)
            content = [prompt, Image.open(uploaded_file)] if uploaded_file else [prompt]
            response = model.generate_content(content)
            
            # Extract text and token data
            ans = response.text
            # usage_metadata contains prompt_token_count, candidates_token_count, total_token_count
            usage = response.usage_metadata
            
            st.markdown(ans)
            st.session_state.messages.append({"role": "assistant", "content": ans})
            st.session_state.total_tokens += usage.total_token_count

    # Update the sidebar with the latest stats
    with token_container:
        st.write(f"**Last Prompt:** {usage.prompt_token_count if 'usage' in locals() else 0}")
        st.write(f"**Last Response:** {usage.candidates_token_count if 'usage' in locals() else 0}")
        st.metric("Total Tokens Used", f"{st.session_state.total_tokens:,}")
        st.caption("Max context: 1,000,000 tokens")

# --- 3. FOOTER ---
if st.session_state.get("password_correct"):
    if st.button("Logout"):
        st.session_state.password_correct = False
        st.rerun()
