import os
import re
import random
import json
from pathlib import Path
from typing import List, Dict
from dotenv import load_dotenv
from langchain.agents import AgentExecutor, create_react_agent
from langchain.prompts import PromptTemplate
from langchain_core.tools import Tool
from langchain_google_genai import ChatGoogleGenerativeAI

# Load environment variables
load_dotenv()

class MemoryManager:
    def __init__(self, user_id: str):
        """Initialize memory management for a specific user"""
        self.user_id = user_id
        self.user_dir = Path("user_data")
        self.user_dir.mkdir(exist_ok=True)
        
        self.conversation_file = self.user_dir / f"{user_id}_conversation.json"
        self.profile_file = self.user_dir / f"{user_id}_profile.json"
        
        # Initialize data structures with default values
        self.conversation = []
        self.profile = {"name": ""}
        
        self._load_data()

    def _load_data(self):
        """Load existing data from files"""
        try:
            if self.conversation_file.exists():
                with open(self.conversation_file, 'r') as f:
                    self.conversation = json.load(f)
            
            if self.profile_file.exists():
                with open(self.profile_file, 'r') as f:
                    self.profile = json.load(f)
        except Exception as e:
            print(f"Warning: Failed to load data - {str(e)}")
            self.conversation = []
            self.profile = {"name": ""}

    def _save_data(self):
        """Save data to files"""
        try:
            with open(self.conversation_file, 'w') as f:
                json.dump(self.conversation, f)
            
            with open(self.profile_file, 'w') as f:
                json.dump(self.profile, f)
        except Exception as e:
            print(f"Error saving data: {str(e)}")

    def set_user_name(self, name: str):
        """Store user name in profile"""
        self.profile['name'] = name
        self._save_data()

    def get_user_name(self) -> str:
        """Get stored user name"""
        return self.profile.get('name', '')

    def add_to_conversation(self, role: str, content: str):
        """Add a message to conversation history"""
        if not content or not isinstance(content, str):
            return
            
        self.conversation.append({
            'role': role,
            'content': content
        })
        self._save_data()

    def get_recent_conversation(self, n: int = 5) -> str:
        """Get recent conversation as formatted string"""
        recent = self.conversation[-n:]
        return "\n".join(f"{msg['role']}: {msg['content']}" for msg in recent)

class TodoTools:
    def __init__(self, memory: MemoryManager):
        self.memory = memory
        self.todos = []
        
    def add_todo(self, task: str) -> str:
        """Add a new task to the todo list"""
        if not task or not isinstance(task, str):
            return "Please provide a valid task"
            
        self.todos.append(task)
        return f"Added: {task}"

    def list_todos(self) -> str:
        """List all current tasks"""
        if not self.todos:
            return "Your to-do list is empty"
        return "\n".join(f"{i+1}. {task}" for i, task in enumerate(self.todos))

    def remove_todo(self, task: str) -> str:
        """Remove a task by index or text"""
        try:
            # Try to remove by index
            index = int(task) - 1
            if 0 <= index < len(self.todos):
                removed = self.todos.pop(index)
                return f"Removed: {removed}"
        except ValueError:
            # Remove by text
            for i, t in enumerate(self.todos):
                if t.lower() == task.lower():
                    removed = self.todos.pop(i)
                    return f"Removed: {removed}"
        return "Task not found"

class TodoChatbot:
    def __init__(self, user_id: str = "default"):
        """Initialize the chatbot with memory and tools"""
        self.user_id = user_id
        self.memory = MemoryManager(user_id)
        self.todo_tools = TodoTools(self.memory)
        self.llm = self._initialize_llm()
        self.agent_executor = self._setup_agent()
        self._initialize_responses()
        
    def _initialize_responses(self):
        """Initialize response templates"""
        self.responses = {
            'greetings': [
                "Hi {name}! How can I assist you today?",
                "Hello {name}! What can I do for you?",
                "Hey there {name}! Ready to tackle some tasks?"
            ],
            'empty_list': [
                "Your to-do list is currently empty, {name}. Want to add something?",
                "No tasks yet, {name}! Shall we create your first one?",
                "All clear, {name}! Your list is ready for new tasks."
            ],
            'nothing_response': [
                "No problem {name}! I'm here when you need me.",
                "Understood {name}! Just say the word when you're ready.",
                "All good {name}! Your list is waiting for when you need it."
            ],
            'goodbye': [
                "Goodbye {name}! Your tasks are saved and ready for next time.",
                "See you later {name}! Don't hesitate to return if you need help.",
                "Bye {name}! Remember I'm here to help with your tasks."
            ],
            'affirmative': [
                "Great {name}! What would you like to do?",
                "Awesome {name}! How can I help?",
                "Perfect {name}! What's next?"
            ]
        }
        
    def _initialize_llm(self) -> ChatGoogleGenerativeAI:
        """Initialize Google Gemini LLM"""
        google_api_key = os.getenv("GOOGLE_API_KEY")
        if not google_api_key:
            raise ValueError("GOOGLE_API_KEY is required in .env file")
        
        return ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            google_api_key=google_api_key,
            temperature=0.3
        )
    
    def _setup_agent(self) -> AgentExecutor:
        """Setup the agent with tools"""
        tools = [
            Tool(
                name="add_todo",
                func=self._safe_add_todo,
                description="Add a new task to the to-do list. Input should be the task description."
            ),
            Tool(
                name="list_todos", 
                func=self._safe_list_todos,
                description="List all current tasks in the to-do list."
            ),
            Tool(
                name="remove_todo",
                func=self._safe_remove_todo,
                description="Remove a task from the to-do list. Input can be task number or description."
            )
        ]
        
        prompt = PromptTemplate.from_template("""
You are a helpful personal assistant that manages to-do lists.

Current Context:
{context}

Available Tools:
{tools}

Tool Names: {tool_names}

Guidelines:
- Always be friendly and helpful
- Use the user's name when known
- Keep responses clear and concise
- For affirmative responses like 'yes', ask what they'd like to do next

Use this format:

Question: the user's input
Thought: your analysis
Action: tool to use
Action Input: input for the tool
Observation: tool result
... (repeat as needed)
Thought: final understanding
Final Answer: your response

Question: {input}
Thought: {agent_scratchpad}""")
        
        agent = create_react_agent(
            llm=self.llm,
            tools=tools,
            prompt=prompt
        )
        
        return AgentExecutor(
            agent=agent,
            tools=tools,
            verbose=False,
            handle_parsing_errors=True
        )
    
    def _get_conversation_context(self) -> str:
        """Get context for the agent"""
        context = []
        if name := self.memory.get_user_name():
            context.append(f"User's name: {name}")
        
        if todos := self.todo_tools.list_todos():
            context.append(f"Current todos:\n{todos}")
        
        if conv := self.memory.get_recent_conversation(3):
            context.append(f"Recent conversation:\n{conv}")
        
        return "\n\n".join(context) if context else "No context available"
    
    def _safe_add_todo(self, task: str) -> str:
        """Safely add a todo"""
        try:
            return self.todo_tools.add_todo(task)
        except Exception as e:
            return f"Error adding task: {str(e)}"
    
    def _safe_list_todos(self, _=None) -> str:
        """Safely list todos"""
        try:
            return self.todo_tools.list_todos()
        except Exception as e:
            return f"Error listing tasks: {str(e)}"
    
    def _safe_remove_todo(self, task: str) -> str:
        """Safely remove a todo"""
        try:
            return self.todo_tools.remove_todo(task)
        except Exception as e:
            return f"Error removing task: {str(e)}"
    
    def chat(self, user_input: str) -> str:
        """Process user input"""
        try:
            if not user_input or not isinstance(user_input, str):
                return "Please enter a valid message."
            
            user_name = self.memory.get_user_name() or "there"
            input_lower = user_input.lower().strip()
            
            # Handle greetings
            if re.match(r'^(hi|hello|hey)', input_lower, re.I):
                return random.choice(self.responses['greetings']).format(name=user_name)
            
            # Handle affirmative responses
            if input_lower in ['yes', 'yeah', 'yep', 'sure']:
                return random.choice(self.responses['affirmative']).format(name=user_name)
            
            # Handle exit
            if input_lower in ['exit', 'quit', 'bye']:
                return random.choice(self.responses['goodbye']).format(name=user_name)
            
            # Process with agent
            response = self.agent_executor.invoke({
                "input": user_input,
                "context": self._get_conversation_context(),
                "tool_names": ", ".join(t.name for t in self.agent_executor.tools)
            })
            
            # Store conversation
            self.memory.add_to_conversation("user", user_input)
            if response and "output" in response:
                self.memory.add_to_conversation("assistant", response["output"])
                return response["output"]
            return "I didn't get that. Could you please rephrase?"
            
        except Exception as e:
            return f"Sorry, I encountered an error. Please try again."

def main():
    """Run the chatbot"""
    print("📝 Todo List Assistant")
    print("=" * 30)
    
    if not os.getenv("GOOGLE_API_KEY"):
        print("Please set GOOGLE_API_KEY in your .env file")
        return
    
    user_name = input("What's your name? ").strip() or "friend"
    chatbot = TodoChatbot(user_name.lower())
    chatbot.memory.set_user_name(user_name)
    
    print(f"\nHello {user_name}! How can I help you today?")
    print("Type 'exit' to quit\n" + "-" * 30)
    
    while True:
        try:
            user_input = input(f"{user_name}: ").strip()
            if not user_input:
                continue
                
            if user_input.lower() in ['exit', 'quit', 'bye']:
                print(chatbot.chat(user_input))
                break
                
            response = chatbot.chat(user_input)
            print(f"Assistant: {response}")
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {str(e)}")
            continue

if __name__ == "__main__":
    main()