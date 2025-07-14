import os
import re
import random
import json
from pathlib import Path
from typing import List, Dict, Optional
from dotenv import load_dotenv
from langchain.agents import AgentExecutor, create_react_agent
from langchain.prompts import PromptTemplate
from langchain_core.tools import Tool
from langchain_google_genai import ChatGoogleGenerativeAI
from memory_manager import MemoryManager
from tools import TodoTools

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
        self._initialize_responses()
        
    def _initialize_responses(self):
        """Initialize response templates"""
        self.responses = {
            'greetings': [
                "Hi {name}! How can I assist you today?",
                "Hello {name}! What can I do for you?",
                "Hey there {name}! Ready to tackle some tasks?",
                "Hey! What can I help you with today?"
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
                description="Add a new task to the to-do list. Input should be the task description as a string."
            ),
            Tool(
                name="list_todos", 
                func=self._safe_list_todos,
                description="List all current tasks in the to-do list. No input required."
            ),
            Tool(
                name="remove_todo",
                func=self._safe_remove_todo,
                description="Remove a task from the to-do list. Input can be task number (1, 2, 3...) or partial task description."
            ),
            Tool(
                name="complete_todo",
                func=self._safe_complete_todo,
                description="Mark a task as completed. Input can be task number (1, 2, 3...) or partial task description."
            ),
            Tool(
                name="clear_todos",
                func=self._safe_clear_todos,
                description="Clear all active tasks from the to-do list. No input required."
            )
        ]
        
        prompt = PromptTemplate.from_template("""
You are a helpful personal assistant that manages to-do lists and holds conversations.

Current Context:
{context}

Available Tools:
{tools}

Tool Names: {tool_names}

Guidelines:
- Always be friendly and conversational
- Remember and use the user's name when known
- Keep responses natural and helpful
- For task management, use the appropriate tools
- When listing todos, present them in a clear, numbered format
- Acknowledge successful actions clearly
- If a user greets you, respond warmly and ask how you can help

Use this format:

Question: the user's input
Thought: I need to understand what the user wants and decide if I need to use any tools
Action: [tool name if needed]
Action Input: [input for the tool if using one]
Observation: [result from tool if used]
... (repeat Thought/Action/Action Input/Observation as needed)
Thought: I now know how to respond to the user
Final Answer: [your conversational response to the user]

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
            handle_parsing_errors=True,
            max_iterations=3
        )
    
    def _get_conversation_context(self) -> str:
        """Get context for the agent"""
        context = []
        
        # Add user name if available
        if name := self.memory.get_user_name():
            context.append(f"User's name: {name}")
        
        # Add recent conversation history
        recent_history = self.memory.get_conversation_history(limit=5)
        if recent_history:
            conv_text = []
            for msg in recent_history[-3:]:  # Last 3 messages
                role = msg.get('role', 'unknown')
                message = msg.get('message', '')
                conv_text.append(f"{role}: {message}")
            if conv_text:
                context.append(f"Recent conversation:\n" + "\n".join(conv_text))
        
        return "\n\n".join(context) if context else "No previous context available"
    
    def _safe_add_todo(self, task: str) -> str:
        """Safely add a todo"""
        try:
            if not task or not task.strip():
                return "Please provide a valid task description."
            return self.todo_tools.add_todo(task.strip())
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
            if not task or not task.strip():
                return "Please specify which task to remove."
            return self.todo_tools.remove_todo(task.strip())
        except Exception as e:
            return f"Error removing task: {str(e)}"
    
    def _safe_complete_todo(self, task: str) -> str:
        """Safely complete a todo"""
        try:
            if not task or not task.strip():
                return "Please specify which task to complete."
            return self.todo_tools.complete_todo(task.strip())
        except Exception as e:
            return f"Error completing task: {str(e)}"
    
    def _safe_clear_todos(self, _=None) -> str:
        """Safely clear all todos"""
        try:
            return self.todo_tools.clear_todos()
        except Exception as e:
            return f"Error clearing tasks: {str(e)}"
    
    def chat(self, user_input: str) -> str:
        """Process user input through the agent"""
        try:
            if not user_input or not isinstance(user_input, str):
                return "Please enter a valid message."
            
            user_input = user_input.strip()
            if not user_input:
                return "Please enter a message."
            
            # Store user input in conversation history
            self.memory.add_to_conversation("user", user_input)
            
            # Process with agent
            response = self.agent_executor.invoke({
                "input": user_input,
                "context": self._get_conversation_context(),
                "tool_names": ", ".join(t.name for t in self.agent_executor.tools)
            })
            
            # Extract and store response
            if response and "output" in response:
                output = response["output"]
                self.memory.add_to_conversation("assistant", output)
                return output
            
            return "I didn't quite understand that. Could you please rephrase?"
            
        except Exception as e:
            error_msg = "Sorry, I encountered an error. Please try again."
            self.memory.add_to_conversation("assistant", error_msg)
            return error_msg
    
    def get_stats(self) -> Dict:
        """Get chatbot statistics"""
        return {
            "memory_stats": self.memory.get_stats(),
            "todo_stats": self.todo_tools.get_stats()
        }

def main():
    """Run the chatbot"""
    print("📝 Todo List Assistant")
    print("=" * 40)
    print("Welcome! I'm your personal todo assistant.")
    print("I can help you manage your tasks and remember our conversations.")
    print("=" * 40)
    
    # Check for API key
    if not os.getenv("GOOGLE_API_KEY"):
        print("❌ ERROR: Please set GOOGLE_API_KEY in your .env file")
        print("Get your free API key from: https://ai.google.dev/")
        return
    
    # Get user name
    user_name = input("What's your name? ").strip()
    if not user_name:
        user_name = "friend"
    
    # Initialize chatbot
    try:
        chatbot = TodoChatbot(user_name.lower())
        chatbot.memory.set_user_name(user_name)
        
        print(f"\nHello {user_name}! How can I help you today?")
        print("You can:")
        print("- Add tasks: 'Add buy groceries to my list'")
        print("- View tasks: 'What's on my todo list?'")
        print("- Remove tasks: 'Remove task 1' or 'Remove buy groceries'")
        print("- Just chat with me!")
        print("- Type 'exit' to quit")
        print("-" * 40)
        
        while True:
            try:
                user_input = input(f"\n{user_name}: ").strip()
                
                if not user_input:
                    continue
                    
                if user_input.lower() in ['exit', 'quit', 'bye', 'goodbye']:
                    response = chatbot.chat(user_input)
                    print(f"Assistant: {response}")
                    break
                
                # Process input through agent
                response = chatbot.chat(user_input)
                print(f"Assistant: {response}")
                
            except KeyboardInterrupt:
                print(f"\n\nGoodbye {user_name}! Your tasks and conversation are saved.")
                break
            except Exception as e:
                print(f"Error: {str(e)}")
                continue
                
    except Exception as e:
        print(f"Failed to initialize chatbot: {str(e)}")
        print("Please check your API key and try again.")

if __name__ == "__main__":
    main()