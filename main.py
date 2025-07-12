from dotenv import load_dotenv
from langchain.agents import AgentExecutor, Tool
from langchain.agents.format_scratchpad.openai_tools import format_to_openai_tool_messages
from langchain.agents.output_parsers import JSONAgentOutputParser
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import AIMessage, HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from tools import TodoTools
from memory_manager import MemoryManager
import os
from typing import List, Dict, Any
import re

# Suppress warnings
load_dotenv()

class Chatbot:
    def __init__(self, user_id: str = "default"):
        self.user_id = user_id
        self.memory = MemoryManager(user_id)
        self.tools = TodoTools(self.memory)
        self.llm = self._initialize_llm()
        self.agent = self._setup_agent()

    def _initialize_llm(self) -> ChatGoogleGenerativeAI:
        """Initialize using Google AI Studio's free tier"""
        google_api_key = os.getenv("GOOGLE_API_KEY")
        if not google_api_key:
            print("\n🔑 Get a FREE API key from:")
            print("1. Visit: https://aistudio.google.com/app/apikey")
            print("2. Create API key (no credit card needed)")
            print("3. Add to .env file as: GOOGLE_API_KEY=your_key_here")
            raise ValueError("API key required for free tier access")
        
        return ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            google_api_key=google_api_key,
            temperature=0.3,
            max_output_tokens=1000
        )

    def _setup_agent(self) -> AgentExecutor:
        """Proper agent setup with correct message formatting"""
        tools = [
            Tool(
                name="add_todo",
                func=self.tools.add_todo,
                description="Add a task to the to-do list. Input should be the exact task text."
            ),
            Tool(
                name="remove_todo",
                func=self.tools.remove_todo,
                description="Remove a task by exact name. Input should be the exact task text."
            ),
            Tool(
                name="list_todos",
                func=self.tools.list_todos,
                description="List all tasks. No input needed."
            )
        ]

        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a helpful to-do list assistant. Follow these rules exactly:
            1. For additions: Respond with "Got it! I've added '[task]' to your list"
            2. For removals: Respond with "Great! I've removed '[task]' from your list" 
            3. For listings: Respond with numbered list:
               1. First task
               2. Second task
            4. Keep responses friendly and concise"""),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ])

        agent = (
            {
                "input": lambda x: x["input"],
                "chat_history": lambda x: x["chat_history"],
                "agent_scratchpad": lambda x: format_to_openai_tool_messages(x["intermediate_steps"]),
            }
            | prompt
            | self.llm.bind_tools(tools)
            | JSONAgentOutputParser()
        )

        return AgentExecutor(
            agent=agent,
            tools=tools,
            verbose=False,
            handle_parsing_errors=True,
            max_iterations=3
        )

    def chat(self, user_input: str) -> str:
        """Process user input with proper error handling"""
        try:
            if not user_input.strip():
                return "Please enter a command."

            # Handle greetings naturally
            if re.match(r'^(hi|hello|hey)\b', user_input, re.I):
                return "Hey! What can I help you with today?"

            # Process through LLM agent
            history = self.memory.get_conversation_history()
            langchain_messages = [
                HumanMessage(content=item["message"]) if item["role"] == "user" 
                else AIMessage(content=item["message"])
                for item in history[-6:]  # Keep conversation context
            ]

            response = self.agent.invoke({
                "input": user_input,
                "chat_history": langchain_messages,
            })

            # Update memory
            self.memory.add_to_conversation("user", user_input)
            self.memory.add_to_conversation("assistant", response["output"])

            return response["output"]

        except Exception as e:
            print(f"System note: {str(e)}")
            return "Let me try that again. Please use: 'add [task]', 'remove [task]', or 'list'"

def main():
    print("📝 To-Do List Assistant")
    print("Type 'exit' to quit\n")
    
    if not os.getenv("GOOGLE_API_KEY"):
        print("Please create a .env file with your Google API key")
        return

    user_id = input("Your name? ").strip() or "friend"
    chatbot = Chatbot(user_id)
    
    print(f"\nHi {user_id}! Here's how to use me:")
    print("- Add tasks: 'Add \"task\"' or 'add task'")
    print("- Remove tasks: 'remove \"task\"' or 'remove 1'")
    print("- View list: 'list' or 'what's on my list?'")
    print("- Exit: 'exit' or 'bye'\n")
    
    while True:
        try:
            user_input = input("You: ").strip()
            if user_input.lower() in ('exit', 'quit', 'bye'):
                print("\nYour list has been saved. Goodbye!")
                break
                
            response = chatbot.chat(user_input)
            print(f"Assistant: {response}")
            
        except KeyboardInterrupt:
            print("\nYour tasks are saved. Come back anytime!")
            break

if __name__ == "__main__":
    main()