import os
import re
import json
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from langchain.agents import AgentExecutor, create_react_agent
from langchain.prompts import PromptTemplate
from langchain_core.tools import Tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.memory import ConversationBufferWindowMemory
from tools import TodoTools
from memory_manager import MemoryManager

# Load environment variables
load_dotenv()

class TodoChatbot:
    def __init__(self, user_id: str = "default"):
        """Initialize the chatbot with memory and tools"""
        self.user_id = user_id
        self.memory = MemoryManager(user_id)
        self.todo_tools = TodoTools(self.memory)
        self.llm = self._initialize_llm()
        self.agent_executor = self._setup_agent()
        
    def _initialize_llm(self) -> ChatGoogleGenerativeAI:
        """Initialize Google Gemini LLM with error handling"""
        google_api_key = os.getenv("GOOGLE_API_KEY")
        if not google_api_key:
            print("\n🔑 Get a FREE API key from:")
            print("1. Visit: https://aistudio.google.com/app/apikey")
            print("2. Create API key (no credit card needed)")
            print("3. Add to .env file as: GOOGLE_API_KEY=your_key_here")
            raise ValueError("GOOGLE_API_KEY is required")
        
        try:
            return ChatGoogleGenerativeAI(
                model="gemini-1.5-flash",
                google_api_key=google_api_key,
                temperature=0.3,
                max_output_tokens=1000
            )
        except Exception as e:
            print(f"❌ Error initializing LLM: {str(e)}")
            print("Please check your API key and internet connection.")
            raise
    
    def _setup_agent(self) -> AgentExecutor:
        """Setup the agent with tools and improved prompt"""
        # Create tools with better error handling
        tools = [
            Tool(
                name="add_todo",
                func=self._safe_add_todo,
                description="Add a new task to the to-do list. Input should be the task description as a string."
            ),
            Tool(
                name="list_todos", 
                func=self._safe_list_todos,
                description="List all current tasks in the to-do list. No input needed - just use empty string."
            ),
            Tool(
                name="remove_todo",
                func=self._safe_remove_todo,
                description="Remove a task from the to-do list. Input should be the task description or task number as a string."
            ),
            Tool(
                name="get_conversation_context",
                func=self._get_conversation_context,
                description="Get recent conversation history for context. No input needed - just use empty string."
            )
        ]
        
        # Enhanced prompt template
        prompt = PromptTemplate.from_template("""You are a helpful personal assistant that manages to-do lists and has conversations.

Your capabilities:
1. Hold conversations and remember the user's name and past messages
2. Manage a personal to-do list using these tools:
   - add_todo: Add a new task to the to-do list
   - list_todos: Show all current tasks
   - remove_todo: Remove a task from the list
   - get_conversation_context: Get conversation history for context

Guidelines:
- Be friendly, conversational, and natural
- Remember the user's name and reference past conversations when relevant
- When adding tasks, be enthusiastic: "Perfect! I've added '[task]' to your to-do list."
- When removing tasks, be encouraging: "Great job! I've removed '[task]' from your list."
- When listing tasks, show them in a clear numbered format
- If a task doesn't exist when trying to remove it, suggest similar tasks if available
- Keep responses concise but warm and helpful
- Use the conversation context to maintain continuity

You have access to the following tools:
{tools}

Tool names: {tool_names}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Question: {input}
Thought: {agent_scratchpad}""")
        
        # Create the ReAct agent
        agent = create_react_agent(
            llm=self.llm,
            tools=tools,
            prompt=prompt
        )
        
        # Create agent executor with improved settings
        agent_executor = AgentExecutor(
            agent=agent,
            tools=tools,
            verbose=False,
            handle_parsing_errors=True,
            max_iterations=5,
            return_intermediate_steps=False,
            early_stopping_method="generate"
        )
        
        return agent_executor
    
    def _safe_add_todo(self, task: str) -> str:
        """Safely add a todo with error handling"""
        try:
            return self.todo_tools.add_todo(task)
        except Exception as e:
            return f"Sorry, I couldn't add that task. Error: {str(e)}"
    
    def _safe_list_todos(self, input_str: str = "") -> str:
        """Safely list todos with error handling"""
        try:
            return self.todo_tools.list_todos()
        except Exception as e:
            return f"Sorry, I couldn't retrieve your tasks. Error: {str(e)}"
    
    def _safe_remove_todo(self, task: str) -> str:
        """Safely remove a todo with error handling"""
        try:
            return self.todo_tools.remove_todo(task)
        except Exception as e:
            return f"Sorry, I couldn't remove that task. Error: {str(e)}"
    
    def _get_conversation_context(self, input_str: str = "") -> str:
        """Get recent conversation history for context"""
        try:
            user_name = self.memory.get_user_name()
            context = f"User name: {user_name}\n"
            
            # Get recent conversation if available
            if hasattr(self.memory, 'get_recent_conversation'):
                recent_conv = self.memory.get_recent_conversation(5)
                if recent_conv:
                    context += "Recent conversation:\n" + recent_conv
            
            return context
        except Exception as e:
            return f"Conversation context unavailable: {str(e)}"
    
    def chat(self, user_input: str) -> str:
        """Process user input and generate response with improved error handling"""
        try:
            if not user_input.strip():
                return "Please enter a message."
            
            # Handle simple greetings more naturally
            greeting_patterns = [
                r'^(hi|hello|hey|greetings?)!?$',
                r'^(good\s+(morning|afternoon|evening))!?$',
                r'^(what\'?s\s+up|how\'?s\s+it\s+going)!?$'
            ]
            
            if any(re.match(pattern, user_input.strip(), re.I) for pattern in greeting_patterns):
                user_name = self.memory.get_user_name()
                if user_name:
                    return f"Hey {user_name}! What can I help you with today?"
                else:
                    return "Hey! What can I help you with today?"
            
            # Handle exit commands
            if user_input.lower().strip() in ['exit', 'quit', 'bye', 'goodbye']:
                user_name = self.memory.get_user_name()
                return f"Goodbye {user_name}! Your tasks and conversation history have been saved."
            
            # Process with agent
            response = self.agent_executor.invoke({"input": user_input})
            
            # Store conversation in memory
            self.memory.add_to_conversation("user", user_input)
            self.memory.add_to_conversation("assistant", response["output"])
            
            return response["output"]
            
        except Exception as e:
            error_msg = str(e)
            print(f"Error in chat: {error_msg}")
            
            # Provide helpful error messages
            if "API" in error_msg or "key" in error_msg.lower():
                return "I'm having trouble connecting to the AI service. Please check your API key."
            elif "network" in error_msg.lower() or "connection" in error_msg.lower():
                return "I'm having network connectivity issues. Please try again."
            else:
                return "I'm having trouble processing that. Could you try rephrasing your request?"

def validate_dependencies():
    """Validate that required dependencies are available"""
    required_modules = ['dotenv', 'langchain', 'langchain_google_genai']
    missing = []
    
    for module in required_modules:
        try:
            __import__(module)
        except ImportError:
            missing.append(module)
    
    if missing:
        print(f"❌ Missing required packages: {', '.join(missing)}")
        print("Install them with: pip install python-dotenv langchain langchain-google-genai")
        return False
    
    return True

def main():
    """Main function to run the chatbot with improved error handling"""
    print("📝 Personal To-Do Assistant")
    print("=" * 30)
    
    # Validate dependencies
    if not validate_dependencies():
        return
    
    # Check for API key
    if not os.getenv("GOOGLE_API_KEY"):
        print("❌ Please set up your Google API key in a .env file")
        print("GOOGLE_API_KEY=your_key_here")
        return
    
    try:
        # Get user name with validation
        user_name = input("What's your name? ").strip()
        if not user_name:
            user_name = "friend"
        
        # Validate user name
        if len(user_name) > 50:
            user_name = user_name[:50]
            print(f"Using shortened name: {user_name}")
        
        # Initialize chatbot
        print("🤖 Initializing your assistant...")
        chatbot = TodoChatbot(user_name)
        
        # Store user name in memory
        chatbot.memory.set_user_name(user_name)
        
        print(f"\n✅ Hi {user_name}! I'm your personal assistant. I can:")
        print("• Have conversations and remember our chat history")
        print("• Add tasks to your to-do list")
        print("• Show your current tasks")
        print("• Remove completed tasks")
        print("• Type 'exit' to quit")
        print("\n💡 Try saying: 'Add buy groceries to my list' or 'What's on my to-do list?'")
        print("-" * 50)
        
        while True:
            try:
                user_input = input(f"\n{user_name}: ").strip()
                
                if user_input.lower() in ['exit', 'quit', 'bye', 'goodbye']:
                    print(f"\n👋 Goodbye {user_name}! Your tasks and conversation history have been saved.")
                    break
                
                if not user_input:
                    continue
                    
                response = chatbot.chat(user_input)
                print(f"🤖 Assistant: {response}")
                
            except KeyboardInterrupt:
                print(f"\n\n👋 Goodbye {user_name}! Your data has been saved.")
                break
            except Exception as e:
                print(f"⚠️ An error occurred: {str(e)}")
                print("Please try again.")
    
    except Exception as e:
        print(f"❌ Failed to initialize chatbot: {str(e)}")
        print("Please check your setup and try again.")

if __name__ == "__main__":
    main()