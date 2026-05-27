import streamlit as st
import httpx
from groq import Groq

# ==============================================================================
# 1. PAGE & SIDEBAR CONFIGURATION
# ==============================================================================
st.set_page_config(page_title="Groq Chat Dashboard", page_icon="💬", layout="wide")

st.sidebar.title("🛠️ Dashboard Settings")

# Gather the Groq API key securely from the UI
api_key = st.sidebar.text_input("Enter your Groq API Key:", type="password")

# Model Selection
model_options = [
    "llama3-8b-8192",
    "llama3-70b-8192",
    "mixtral-8x7b-32768",
    "gemma2-9b-it"
]
selected_model = st.sidebar.selectbox("Choose a Model:", model_options)

# System Prompt Customization
system_prompt = st.sidebar.text_area(
    "System Prompt (AI Persona):", 
    value="You are a helpful, witty, and concise AI assistant."
)

# Clear Chat Button
if st.sidebar.button("🧹 Clear Chat History"):
    st.session_state.messages = []
    st.rerun()

# ==============================================================================
# 2. INITIALIZE SESSION STATE & HEADER
# ==============================================================================
if "messages" not in st.session_state:
    st.session_state.messages = []

st.title("💬 Groq Chat Dashboard")
st.write("Experience lightning-fast inference powered by Groq LPU™ technology.")
st.divider()

# Display existing chat history on rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# ==============================================================================
# 3. CHAT INPUT & EXECUTION LOGIC
# ==============================================================================
if prompt := st.chat_input("What's on your mind?"):
    
    # Validation Guardrail: Ensure API key isn't empty or whitespace
    if not api_key or api_key.strip() == "":
        st.error("❌ Please enter your Groq API Key in the sidebar before typing a message!")
    else:
        try:
            # Fixes the 'proxies' TypeError by passing a clean, explicit HTTP client
            custom_http_client = httpx.Client()
            
            # Initialize Groq client with the safe HTTP configuration
            client = Groq(
                api_key=api_key.strip(),
                http_client=custom_http_client
            )
            
            # Display user message dynamically in the UI
            with st.chat_message("user"):
                st.markdown(prompt)
            
            # Save user message to persistent session state memory
            st.session_state.messages.append({"role": "user", "content": prompt})

            # Formulate the payload tracking the overall conversation context
            full_messages = [{"role": "system", "content": system_prompt}] + st.session_state.messages

            # Initialize assistant's visual box and stream incoming chunks
            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                full_response = ""
                
                # Fetch token stream directly from Groq endpoints
                completion = client.chat.completions.create(
                    model=selected_model,
                    messages=full_messages,
                    temperature=0.7,
                    max_tokens=1024,
                    stream=True,  # Keeps connections alive for rapid rendering
                )
                
                # Process chunks dynamically as they hit the server
                for chunk in completion:
                    chunk_text = chunk.choices[0].delta.content or ""
                    full_response += chunk_text
                    message_placeholder.markdown(full_response + "▌")
                
                # Finalize markdown text and strip cursor blinking marker
                message_placeholder.markdown(full_response)
                
                # Commit the model's response to history
                st.session_state.messages.append({"role": "assistant", "content": full_response})
                
        except Exception as e:
            st.error(f"⚠️ An error occurred during API execution: {e}")
