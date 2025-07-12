from dotenv import load_dotenv
from langchain.agents import AgentExecutor, Tool
from langchain.agents.format_scratchpad import format_log_to_str
from langchain.agents.output_parsers import JSONAgentOutputParser
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import AIMessage, HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from tools import TodoTools
from memory_manager import MemoryManager
import os

load_dotenv()

class Chatbot:
    def __init__(self, user_id: str = "default"):
        self.memory = MemoryManager(user_id)
        self.tools = TodoTools(self.memory)
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-pro",
            google_api_key=os.getenv("GOOGLE_API_KEY"),
            temperature=0.3
        )
        self.agent = self._setup_agent()

    def _setup_agent(self):
        # Define available tools
        tools = [
            Tool(
                name="add_todo",
                func=self.tools.add_todo,
                description="Add a task to the user's to-do list. Input should be the task string."
            ),
            Tool(
                name="remove_todo",
                func=self.tools.remove_todo,
                description="Remove a task from the user's to-do list. Input should be the task string."
            ),
            Tool(
                name="list_todos",
                func=self.tools.list_todos,
                description="List all tasks in the user's to-do list. No input needed."
            )
        ]

        # Set up prompt template
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a helpful AI assistant. You can help manage a to-do list.
            You have access to tools to add, remove, and list to-do items.
            Be friendly and concise in your responses.
            Current conversation history: {history}"""),
            MessagesPlaceholder(variable_name="chat_history"),
            ("user", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ])

        # Bind tools to LLM
        llm_with_tools = self.llm.bind_tools(tools)

        # Define agent pipeline
        agent = (
            {
                "input": lambda x: x["input"],
                "chat_history": lambda x: x["chat_history"],
                "agent_scratchpad": lambda x: format_log_to_str(x["intermediate_steps"]),
                "history": lambda x: self._format_history(x["chat_history"])
            }
            | prompt
            | llm_with_tools
            | JSONAgentOutputParser()
        )

        return AgentExecutor(agent=agent, tools=tools, verbose=True)

    def _format_history(self, messages):
        return "\n".join(
            f"{'User' if isinstance(msg, HumanMessage) else 'AI'}: {msg.content}"
            for msg in messages
        )

    def chat(self, user_input: str):
        # Get conversation history
        history = self.memory.get_conversation_history()
        langchain_messages = []
        
        for item in history:
            if item["role"] == "user":
                langchain_messages.append(HumanMessage(content=item["message"]))
            else:
                langchain_messages.append(AIMessage(content=item["message"]))
        
        # Process input
        response = self.agent.invoke({
            "input": user_input,
            "chat_history": langchain_messages
        })
        
        # Update memory
        self.memory.add_to_conversation("user", user_input)
        self.memory.add_to_conversation("assistant", response["output"])
        
        return response["output"]

def main():
    print("Welcome to Snello Chatbot!")
    user_id = input("Please enter your user ID (default: 'default'): ") or "default"
    chatbot = Chatbot(user_id)
    
    print("\nHow can I help you today? (Type 'exit' to quit)")
    while True:
        user_input = input("You: ")
        if user_input.lower() == 'exit':
            break
        response = chatbot.chat(user_input)
        print(f"AI: {response}")

if __name__ == "__main__":
    main()