from dotenv import load_dotenv
from langchain.agents import AgentExecutor, create_react_agent
from langchain.prompts import PromptTemplate
from langchain_core.tools import Tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.memory import ConversationBufferWindowMemory
from tools import TodoTools
from memory_manager import MemoryManager
import os
import re

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
        """Initialize Google Gemini LLM"""
        google_api_key = os.getenv("GOOGLE_API_KEY")
        if not google_api_key:
            print("\n🔑 Get a FREE API key from:")
            print("1. Visit: https://aistudio.google.com/app/apikey")
            print("2. Create API key (no credit card needed)")
            print("3. Add to .env file as: GOOGLE_API_KEY=your_key_here")
            raise ValueError("GOOGLE_API_KEY is required")
        
        return ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            google_api_key=google_api_key,
            temperature=0.3,
            max_output_tokens=1000
        )
    
    def _setup_agent(self) -> AgentExecutor:
        """Setup the agent with tools and prompt using the modern approach"""
        # Create tools
        tools = [
            Tool(
                name="add_todo",
                func=self.todo_tools.add_todo,
                description="Add a new task to the to-do list. Input should be the task description."
            ),
            Tool(
                name="list_todos", 
                func=self.todo_tools.list_todos,
                description="List all current tasks in the to-do list. No input needed."
            ),
            Tool(
                name="remove_todo",
                func=self.todo_tools.remove_todo,
                description="Remove a task from the to-do list. Input should be the task description or number."
            )
        ]
        
        # Create prompt template
        prompt = PromptTemplate.from_template("""You are a helpful personal assistant that manages to-do lists and has conversations.

Your capabilities:
1. Hold conversations and remember the user's name and past messages
2. Manage a personal to-do list using these tools:
   - add_todo: Add a new task to the to-do list
   - list_todos: Show all current tasks
   - remove_todo: Remove a task from the list

Guidelines:
- Be friendly and conversational
- Remember the user's name and reference past conversations when relevant
- When adding tasks, respond with: "Got it! I've added '[task]' to your to-do list."
- When removing tasks, respond with: "Great! I've removed '[task]' from your list."
- When listing tasks, show them in a numbered format
- If a task doesn't exist when trying to remove it, let the user know politely
- Keep responses concise but helpful

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
        
        # Create agent executor
        agent_executor = AgentExecutor(
            agent=agent,
            tools=tools,
            verbose=False,
            handle_parsing_errors=True,
            max_iterations=3,
            return_intermediate_steps=False
        )
        
        return agent_executor
    
    def chat(self, user_input: str) -> str:
        """Process user input and generate response"""
        try:
            if not user_input.strip():
                return "Please enter a message."
            
            # Handle simple greetings
            if re.match(r'^(hi|hello|hey)!?$', user_input.strip(), re.I):
                user_name = self.memory.get_user_name()
                if user_name:
                    return f"Hey {user_name}! What can I help you with today?"
                else:
                    return "Hey! What can I help you with today?"
            
            # Process with agent
            response = self.agent_executor.invoke({"input": user_input})
            
            # Store conversation in memory
            self.memory.add_to_conversation("user", user_input)
            self.memory.add_to_conversation("assistant", response["output"])
            
            return response["output"]
            
        except Exception as e:
            print(f"Error: {str(e)}")
            return "I'm having trouble processing that. Could you try rephrasing your request?"

def main():
    """Main function to run the chatbot"""
    print("📝 Personal To-Do Assistant")
    print("=" * 30)
    
    # Check for API key
    if not os.getenv("GOOGLE_API_KEY"):
        print("❌ Please set up your Google API key in a .env file")
        print("GOOGLE_API_KEY=your_key_here")
        return
    
    # Get user name
    user_name = input("What's your name? ").strip()
    if not user_name:
        user_name = "friend"
    
    # Initialize chatbot
    chatbot = TodoChatbot(user_name)
    
    # Store user name in memory
    chatbot.memory.set_user_name(user_name)
    
    print(f"\nHi {user_name}! I'm your personal assistant. I can:")
    print("• Have conversations and remember our chat history")
    print("• Add tasks to your to-do list")
    print("• Show your current tasks")
    print("• Remove completed tasks")
    print("• Type 'exit' to quit")
    print("\nTry saying: 'Add buy groceries to my list' or 'What's on my to-do list?'")
    print("-" * 50)
    
    while True:
        try:
            user_input = input(f"\n{user_name}: ").strip()
            
            if user_input.lower() in ['exit', 'quit', 'bye', 'goodbye']:
                print(f"\nGoodbye {user_name}! Your tasks and conversation history have been saved.")
                break
            
            if not user_input:
                continue
                
            response = chatbot.chat(user_input)
            print(f"Assistant: {response}")
            
        except KeyboardInterrupt:
            print(f"\n\nGoodbye {user_name}! Your data has been saved.")
            break
        except Exception as e:
            print(f"An error occurred: {str(e)}")
            print("Please try again.")

if __name__ == "__main__":
    main()