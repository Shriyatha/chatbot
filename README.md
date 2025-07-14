# 🤖 AI Todo Assistant - Snello SDE Internship Project

A conversational AI chatbot that manages personal to-do lists using an agentic architecture with Google Gemini API, LangChain, and Streamlit.

## 🎯 Project Overview

This project implements an intelligent todo assistant that can:
- Hold natural conversations while remembering user context
- Manage personal to-do lists through LLM tool calls
- Persist conversation history and todo data
- Provide a modern, interactive web interface

## 🏗️ Architecture

### System Design
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Streamlit     │    │   TodoChatbot   │    │  Memory Manager │
│   Frontend      │◄──►│   (Main Agent)  │◄──►│   (Persistence) │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │   LangChain     │
                       │   Agent         │
                       │   Executor      │
                       └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │   Todo Tools    │
                       │   (Actions)     │
                       └─────────────────┘
```

### Core Components

1. **TodoChatbot (main.py)** - Central agent orchestrator
   - Initializes Google Gemini LLM via LangChain
   - Sets up ReAct agent with custom tools
   - Manages conversation flow and context
   - Handles error recovery and user interactions

2. **MemoryManager (memory_manager.py)** - Persistent storage handler
   - Stores conversation history in JSON format
   - Manages user profiles and preferences
   - Provides backup and recovery mechanisms
   - Handles file-based persistence with error handling

3. **TodoTools (tools.py)** - Task management operations
   - Implements CRUD operations for todos
   - Supports task completion tracking
   - Provides priority and tagging features
   - Handles duplicate detection and validation

4. **Streamlit UI (app.py)** - Web interface
   - Modern dark theme with animations
   - Real-time chat interface
   - Quick action buttons
   - Mobile-responsive design

## 🔧 Technical Implementation

### LLM Integration
- **Model**: Google Gemini 1.5 Flash via LangChain
- **Framework**: LangChain ReAct Agent pattern
- **Temperature**: 0.3 for consistent responses
- **Tool Integration**: Custom tool definitions with error handling

### Memory Architecture
- **Conversation History**: JSON-based persistent storage
- **User Profiles**: Separate profile management
- **Context Window**: Maintains last 5 conversation turns
- **Backup System**: Automatic file backups with corruption recovery

### Tool Definitions
```python
# Core tools registered with the LLM agent
tools = [
    add_todo(task: str) -> str,
    list_todos() -> str,
    remove_todo(task_ref: Union[str, int]) -> str,
    complete_todo(task_ref: Union[str, int]) -> str,
    clear_todos() -> str
]
```

## 🚀 Setup Instructions

### Prerequisites
- Python 3.8+
- Google AI Studio API key (free tier)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd todo-chatbot
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   # Create .env file
   echo "GOOGLE_API_KEY=your_google_api_key_here" > .env
   ```

4. **Get Google AI Studio API Key**
   - Visit [Google AI Studio](https://ai.google.dev/)
   - Create a new project
   - Generate API key
   - Add to `.env` file

## 🎮 Usage

### Web Interface (Recommended)
```bash
streamlit run app.py
```
- Opens at `http://localhost:8501`
- Enter your name to start chatting
- Use natural language for todo management

### Command Line Interface
```bash
python3 main.py
```

### Example Conversations

**Basic Todo Management:**
```
User: Add "Buy groceries" to my todo list
Assistant: ✅ Added: Buy groceries

User: What's on my list?
Assistant: 📝 Your current to-do list:
1. Buy groceries

User: Remove task 1
Assistant: ✅ Removed: Buy groceries
```

**Natural Language Processing:**
```
User: I need to remember to call mom tomorrow
Assistant: ✅ Added: call mom tomorrow

User: Show me what I need to do
Assistant: 📝 Your current to-do list:
1. call mom tomorrow

User: I finished calling mom
Assistant: ✅ Completed: call mom tomorrow
```

**Conversation Memory:**
```
User: Hi, I'm John
Assistant: Hi John! How can I help you today?

User: Add a task about the project
Assistant: ✅ Added: task about the project

[Later in conversation]
User: What did I add earlier?
Assistant: You added "task about the project" to your list, John!
```

## 💾 Data Persistence

### Storage Structure
```
user_data/
├── {user_id}_conversation.json    # Chat history
├── {user_id}_profile.json         # User preferences
├── {user_id}_todos.json          # Todo items
└── backups/                      # Automatic backups
    ├── {user_id}_conversation_backup_*.json
    └── {user_id}_todos_backup_*.json
```

### Memory Features
- **Conversation History**: Stores last 100 messages per user
- **User Profiles**: Remembers names and preferences
- **Todo Persistence**: Maintains active and completed tasks
- **Backup System**: Automatic file backups on updates
- **Error Recovery**: Handles corrupted files gracefully

## 🔨 Tool Call Implementation

### Tool Registration
Each tool is registered with the LangChain agent using the Tool class:

```python
Tool(
    name="add_todo",
    func=self._safe_add_todo,
    description="Add a new task to the to-do list. Input should be the task description as a string."
)
```

### Agent Prompt Template
The agent uses a ReAct (Reasoning + Acting) pattern:
```
Question: {user_input}
Thought: I need to understand what the user wants
Action: [tool_name]
Action Input: [tool_input]
Observation: [tool_result]
Final Answer: [conversational_response]
```

### Error Handling
- Graceful tool failure recovery
- Input validation and sanitization
- Comprehensive logging system
- User-friendly error messages

## 📊 Features

### Core Functionality
- ✅ **Conversation Memory**: Remembers user name and chat history
- ✅ **Todo Management**: Add, list, remove, complete tasks
- ✅ **LLM Tool Calls**: Seamless integration with Gemini API
- ✅ **Persistent Storage**: File-based data persistence
- ✅ **Agentic Architecture**: Clear separation of concerns

### Advanced Features
- 🎨 **Modern UI**: Dark theme with smooth animations
- 🔄 **Real-time Updates**: Live chat interface
- 📱 **Mobile Responsive**: Works on all devices
- 🛡️ **Error Recovery**: Robust error handling
- 📈 **Usage Analytics**: Conversation and todo statistics
- 🏷️ **Task Organization**: Priority levels and tagging support

## 🚧 Limitations & Future Improvements

### Current Limitations
1. **Single User Sessions**: No multi-user authentication
2. **Local Storage Only**: No cloud synchronization
3. **Basic Search**: Limited conversation search capabilities
4. **No Task Scheduling**: No due dates or reminders

### Planned Enhancements
1. **User Authentication**: Multi-user support with secure login
2. **Cloud Integration**: Supabase/Firebase integration
3. **Advanced Search**: Full-text search across conversations
4. **Task Scheduling**: Due dates, reminders, and recurring tasks
5. **Export Features**: Export todos to various formats
6. **Voice Interface**: Speech-to-text integration
7. **Mobile App**: React Native mobile application

## 🧪 Testing

### Manual Testing Scenarios
1. **Basic Conversation Flow**
   - Start new conversation
   - Add/remove/list todos
   - Verify memory persistence

2. **Error Handling**
   - Invalid inputs
   - Corrupted data files
   - Network connectivity issues

3. **UI/UX Testing**
   - Responsive design
   - Animation performance
   - Accessibility features

## 📝 Development Notes

### Commit History
This project maintains regular commits (every 1-2 hours) showing development progress:
- Initial project setup and structure
- LangChain agent implementation
- Memory management system
- Todo tools development
- Streamlit UI creation
- Testing and refinement

### Code Quality
- **Type Hints**: Comprehensive type annotations
- **Documentation**: Detailed docstrings and comments
- **Error Handling**: Robust exception management
- **Logging**: Structured logging throughout
- **Modularity**: Clear separation of concerns

## 🔗 Dependencies

```
streamlit>=1.28.0
langchain>=0.1.0
langchain-google-genai>=0.0.6
python-dotenv>=1.0.0
nest-asyncio>=1.5.8
```

## 👨‍💻 Author

Built for Snello SDE Internship Assignment - demonstrating agentic AI system design with practical todo management capabilities.

---

*This project showcases modern AI agent architecture, persistent memory management, and user-friendly interface design. The implementation demonstrates understanding of LLM integration, tool calling, and conversational AI principles.*