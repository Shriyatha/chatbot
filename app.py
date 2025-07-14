import streamlit as st
import asyncio
import nest_asyncio
from main import TodoChatbot
from dotenv import load_dotenv
import time
from typing import Optional

# Fix event loop issues
nest_asyncio.apply()
load_dotenv()

# --- Streamlit UI Configuration ---
st.set_page_config(
    page_title="✨ Todo AI Assistant",
    page_icon="🤖",
    layout="centered",
    initial_sidebar_state="expanded"
)

# Custom Dark Theme CSS
st.markdown("""
    <style>
    :root {
        --primary: #7f5af0;
        --secondary: #2cb67d;
        --dark-bg: #16161a;
        --card-bg: #242629;
        --text-primary: #fffffe;
        --text-secondary: #94a1b2;
        --accent: #7f5af0;
    }
    
    .stApp {
        background-color: var(--dark-bg);
        color: var(--text-primary);
    }
    
    .stChatMessage {
        padding: 16px 20px;
        border-radius: 18px;
        margin-bottom: 12px;
        max-width: 85%;
        animation: fadeIn 0.3s ease-out;
        font-family: 'Segoe UI', system-ui, sans-serif;
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    [data-testid="stChatMessage-user"] {
        background-color: var(--card-bg);
        margin-left: auto;
        border: 1px solid #2e3033;
        color: var(--text-primary);
        border-bottom-right-radius: 4px;
    }
    
    [data-testid="stChatMessage-assistant"] {
        background: linear-gradient(135deg, var(--primary) 0%, #6c43e0 100%);
        color: white;
        border-bottom-left-radius: 4px;
    }
    
    .stButton>button {
        background: linear-gradient(135deg, var(--primary) 0%, #6c43e0 100%);
        color: white;
        border-radius: 12px;
        padding: 8px 16px;
        border: none;
        font-weight: 500;
        transition: all 0.2s;
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(127, 90, 240, 0.4);
    }
    
    .stTextInput>div>div>input {
        border-radius: 12px;
        padding: 12px 16px;
        background-color: var(--card-bg);
        color: var(--text-primary);
        border: 1px solid #2e3033;
    }
    
    .sidebar .sidebar-content {
        background-color: var(--card-bg);
        border-right: 1px solid #2e3033;
    }
    
    .stSpinner>div {
        background: linear-gradient(135deg, var(--primary) 0%, #6c43e0 100%);
    }
    
    .chat-container {
        height: calc(100vh - 200px);
        overflow-y: auto;
        padding: 0 16px;
    }
    
    .typing-indicator {
        display: inline-block;
        padding: 12px 16px;
        background: var(--card-bg);
        border-radius: 18px;
        color: var(--text-primary);
        border: 1px solid #2e3033;
    }
    
    .typing-dot {
        display: inline-block;
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background-color: var(--primary);
        margin: 0 2px;
        animation: typingAnimation 1.4s infinite ease-in-out;
    }
    
    h1, h2, h3, h4, h5, h6 {
        color: var(--text-primary) !important;
    }
    
    .stMarkdown p {
        color: var(--text-primary);
    }
    
    .stTextInput>div>div>input::placeholder {
        color: var(--text-secondary);
    }
    
    hr {
        border-color: #2e3033;
    }
    
    /* Scrollbar styling */
    ::-webkit-scrollbar {
        width: 8px;
    }
    ::-webkit-scrollbar-track {
        background: var(--card-bg);
    }
    ::-webkit-scrollbar-thumb {
        background: var(--primary);
        border-radius: 4px;
    }
    </style>
""", unsafe_allow_html=True)

# --- Chatbot Initialization ---
def initialize_chatbot() -> Optional[TodoChatbot]:
    """Initialize chatbot with proper event loop handling"""
    if "chatbot" not in st.session_state:
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            st.session_state.chatbot = TodoChatbot(st.session_state.user_name.lower())
            st.session_state.chatbot.memory.set_user_name(st.session_state.user_name)
            
            if "messages" not in st.session_state:
                st.session_state.messages = [
                    {"role": "assistant", "content": f"Hi {st.session_state.user_name}! I'm your AI Todo Assistant. How can I help you today? 🌟"}
                ]
            return st.session_state.chatbot
        except Exception as e:
            st.error(f"Failed to initialize chatbot: {str(e)}")
            return None
        finally:
            loop.close()
    return st.session_state.chatbot

def show_typing_indicator():
    """Display typing indicator animation"""
    with st.empty():
        st.markdown("""
        <div class="typing-indicator">
            <span class="typing-dot"></span>
            <span class="typing-dot"></span>
            <span class="typing-dot"></span>
        </div>
        """, unsafe_allow_html=True)
        time.sleep(1.5)

# --- Main App ---
def main():
    st.title("✨ AI Todo Assistant")
    st.caption("Your smart productivity companion powered by AI")
    
    # User initialization
    if "user_name" not in st.session_state:
        with st.sidebar:
            st.image("https://cdn-icons-png.flaticon.com/512/4712/4712035.png", width=120)
            st.subheader("Welcome! 👋")
            name = st.text_input("What should I call you?", placeholder="Enter your name")
            
            col1, col2 = st.columns([1, 1])
            with col1:
                if st.button("Start Chatting", use_container_width=True, disabled=not name.strip()):
                    st.session_state.user_name = name.strip()
                    initialize_chatbot()
                    st.rerun()
            with col2:
                if st.button("Try Demo", use_container_width=True):
                    st.session_state.user_name = "Guest"
                    initialize_chatbot()
                    st.rerun()
        
        # Hero section
        st.markdown("""
        <div style="text-align: center; padding: 40px 0;">
            <h2 style="color: #7f5af0;">Your Smart Todo Assistant</h2>
            <p style="font-size: 1.1rem; color: #94a1b2;">
                Manage tasks, stay organized, and boost productivity with AI<br>
                Try saying: <i>"Add buy groceries to my list"</i> or <i>"What's on my to-do list?"</i>
            </p>
            <img src="https://cdn-icons-png.flaticon.com/512/4712/4712139.png" width="300" style="margin-top: 20px;">
        </div>
        """, unsafe_allow_html=True)
        return
    
    # Main chat interface
    chatbot = initialize_chatbot()
    if not chatbot:
        return
    
    # Display chat history
    chat_container = st.container()
    with chat_container:
        for message in st.session_state.messages:
            avatar = "🤖" if message["role"] == "assistant" else "👤"
            with st.chat_message(message["role"], avatar=avatar):
                st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input(f"Message {st.session_state.user_name}'s assistant..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Get AI response
        with st.spinner(""):
            show_typing_indicator()
            response = chatbot.chat(prompt)
        
        # Add assistant response
        st.session_state.messages.append({"role": "assistant", "content": response})
        
        # Rerun to update UI
        st.rerun()
    
    # Sidebar controls
    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/4712/4712035.png", width=80)
        st.subheader(f"Hello, {st.session_state.user_name}!")
        st.markdown("---")
        
        # Quick action buttons
        st.markdown("**Quick Actions**")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📝 Show Todos", use_container_width=True):
                response = chatbot.chat("Show my todos")
                st.session_state.messages.append({"role": "assistant", "content": response})
                st.rerun()
        with col2:
            if st.button("➕ Add Todo", use_container_width=True):
                st.session_state.messages.append({"role": "user", "content": "Add a new task"})
                st.rerun()
        
        st.markdown("---")
        
        # Chat management
        st.markdown("**Chat Settings**")
        if st.button("🧹 Clear Chat", use_container_width=True):
            st.session_state.messages = [
                {"role": "assistant", "content": f"Chat cleared! How can I help you, {st.session_state.user_name}? 💬"}
            ]
            st.rerun()
        
        if st.button("🔄 Restart", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
        
        st.markdown("---")
        st.caption("""
        **Tips:**
        - Try natural language like "Add buy milk to my list"
        - Say "Remove task 1" to delete items
        - Type "exit" to end the conversation
        """)

if __name__ == "__main__":
    main()