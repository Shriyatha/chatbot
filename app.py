import streamlit as st
import asyncio
import nest_asyncio
from main import TodoChatbot
from dotenv import load_dotenv
import time

# Fix event loop issues
nest_asyncio.apply()

# Load environment variables
load_dotenv()

# --- Streamlit UI Configuration ---
st.set_page_config(
    page_title="✨ Todo AI Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS styling
st.markdown("""
    <style>
    .stChatMessage {
        padding: 12px 16px;
        border-radius: 12px;
        margin-bottom: 8px;
        box-shadow: 0 1px 2px rgba(0,0,0,0.1);
    }
    [data-testid="stChatMessage-user"] {
        background-color: #f0f2f6;
        margin-left: auto;
    }
    [data-testid="stChatMessage-assistant"] {
        background-color: #f8f9fa;
    }
    .stButton>button {
        background: #4f46e5;
        color: white;
        border-radius: 8px;
    }
    </style>
""", unsafe_allow_html=True)

# --- Chatbot Initialization ---
def initialize_chatbot():
    """Initialize chatbot with proper event loop handling"""
    if "chatbot" not in st.session_state:
        # Create new event loop for async operations
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            st.session_state.chatbot = TodoChatbot(st.session_state.user_name)
            st.session_state.chatbot.memory.set_user_name(st.session_state.user_name)
            st.session_state.messages = [
                {"role": "assistant", "content": f"Hi {st.session_state.user_name}! How can I help you today?"}
            ]
        finally:
            loop.close()

# --- Main App ---
def main():
    st.title("📝 AI Todo Assistant")
    
    # User initialization
    if "user_name" not in st.session_state:
        with st.sidebar:
            name = st.text_input("What's your name?")
            if st.button("Start Chatting") and name.strip():
                st.session_state.user_name = name.strip()
                initialize_chatbot()
                st.rerun()
        return
    
    # Display chat history
    for message in st.session_state.get("messages", []):
        st.chat_message(message["role"]).markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Type your message..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.chat_message("user").markdown(prompt)
        
        # Get AI response
        with st.spinner("Thinking..."):
            response = st.session_state.chatbot.chat(prompt)
        
        # Add assistant response
        st.session_state.messages.append({"role": "assistant", "content": response})
        st.chat_message("assistant").markdown(response)
    
    # Sidebar controls
    with st.sidebar:
        st.subheader(f"Hello, {st.session_state.user_name}!")
        
        if st.button("Show My Todos"):
            response = st.session_state.chatbot.chat("Show my todos")
            st.session_state.messages.append({"role": "assistant", "content": response})
            st.rerun()
            
        if st.button("Clear Chat"):
            st.session_state.messages = [
                {"role": "assistant", "content": f"Chat cleared! How can I help you, {st.session_state.user_name}?"}
            ]
            st.rerun()

if __name__ == "__main__":
    main()