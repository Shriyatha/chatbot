#!/usr/bin/env python3
"""
Test script for the Personal Todo Assistant
"""

import os
import sys
import traceback
from dotenv import load_dotenv

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

load_dotenv()

def test_memory_manager():
    """Test the memory manager"""
    print("Testing Memory Manager...")
    try:
        from memory_manager import MemoryManager
        import uuid
        
        # Test memory manager with unique user ID to avoid conflicts
        test_user_id = f"test_user_{uuid.uuid4().hex[:8]}"
        memory = MemoryManager(test_user_id)
        print("  ✓ MemoryManager created")
        
        # Test conversation
        memory.add_to_conversation("user", "Hello")
        memory.add_to_conversation("assistant", "Hi there!")
        print("  ✓ Conversation messages added")
        
        history = memory.get_conversation_history()
        print(f"  ✓ Retrieved {len(history)} messages")
        
        # Detailed assertions with better error messages
        if len(history) != 2:
            print(f"  ❌ Expected 2 messages, got {len(history)}")
            return False
        
        if history[0]["role"] != "user":
            print(f"  ❌ Expected first message role to be 'user', got '{history[0]['role']}'")
            return False
        
        if history[0]["message"] != "Hello":
            print(f"  ❌ Expected first message to be 'Hello', got '{history[0]['message']}'")
            return False
        
        print("  ✓ Conversation history verified")
        
        # Test todos
        memory.save_todos(["Test task 1", "Test task 2"])
        print("  ✓ Todos saved")
        
        todos = memory.get_todos()
        print(f"  ✓ Retrieved {len(todos)} todos")
        
        if len(todos) != 2:
            print(f"  ❌ Expected 2 todos, got {len(todos)}")
            return False
        
        if "Test task 1" not in todos:
            print(f"  ❌ 'Test task 1' not found in todos: {todos}")
            return False
        
        print("  ✓ Todos verified")
        
        # Test user profile
        memory.set_user_name("Test User")
        print("  ✓ User name set")
        
        name = memory.get_user_name()
        print(f"  ✓ Retrieved user name: '{name}'")
        
        if name != "Test User":
            print(f"  ❌ Expected user name to be 'Test User', got '{name}'")
            return False
        
        print("  ✓ User profile verified")
        
        print("✅ Memory Manager tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Memory Manager test failed: {e}")
        traceback.print_exc()
        return False

def test_todo_tools():
    """Test the todo tools"""
    print("Testing Todo Tools...")
    try:
        from memory_manager import MemoryManager
        from tools import TodoTools
        import uuid
        
        # Setup with unique user ID
        test_user_id = f"test_user_{uuid.uuid4().hex[:8]}"
        memory = MemoryManager(test_user_id)
        tools = TodoTools(memory)
        print("  ✓ TodoTools created")
        
        # Test add
        result = tools.add_todo("Test task")
        print(f"  ✓ Add result: {result}")
        
        if "added" not in result.lower():
            print(f"  ❌ Expected 'added' in result, got: {result}")
            return False
        
        # Test list
        result = tools.list_todos()
        print(f"  ✓ List result: {result}")
        
        if "Test task" not in result:
            print(f"  ❌ Expected 'Test task' in result, got: {result}")
            return False
        
        # Test remove
        result = tools.remove_todo("Test task")
        print(f"  ✓ Remove result: {result}")
        
        if "removed" not in result.lower():
            print(f"  ❌ Expected 'removed' in result, got: {result}")
            return False
        
        # Test empty list
        result = tools.list_todos()
        print(f"  ✓ Empty list result: {result}")
        
        if "empty" not in result.lower():
            print(f"  ❌ Expected 'empty' in result, got: {result}")
            return False
        
        print("✅ Todo Tools tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Todo Tools test failed: {e}")
        traceback.print_exc()
        return False

def test_api_key():
    """Test API key setup"""
    print("Testing API Key Setup...")
    
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("❌ GOOGLE_API_KEY not found in environment")
        print("  → Create a .env file with: GOOGLE_API_KEY=your_actual_key_here")
        return False
    
    if api_key == "your_google_api_key_here":
        print("❌ Please set your actual Google API key in .env file")
        print("  → Replace 'your_google_api_key_here' with your real API key")
        return False
    
    print("✅ API Key found!")
    return True

def test_imports():
    """Test all imports"""
    print("Testing Imports...")
    try:
        # Test core imports
        print("  → Testing LangChain imports...")
        from langchain.agents import AgentExecutor, Tool
        from langchain.agents.format_scratchpad.openai_tools import format_to_openai_tool_messages
        from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
        from langchain_core.messages import AIMessage, HumanMessage
        from langchain_google_genai import ChatGoogleGenerativeAI
        print("  ✓ LangChain imports successful")
        
        # Test local imports
        print("  → Testing local imports...")
        from memory_manager import MemoryManager
        print("  ✓ MemoryManager imported")
        from tools import TodoTools
        print("  ✓ TodoTools imported")
        
        print("✅ All imports successful!")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("  → Try running: pip install -r requirements.txt")
        return False

def check_file_structure():
    """Check if all required files exist"""
    print("Checking File Structure...")
    
    required_files = [
        "memory_manager.py",
        "tools.py",
        ".env"
    ]
    
    missing_files = []
    
    for file in required_files:
        if os.path.exists(file):
            print(f"  ✓ {file} found")
        else:
            print(f"  ❌ {file} missing")
            missing_files.append(file)
    
    if missing_files:
        print(f"❌ Missing files: {missing_files}")
        return False
    
    print("✅ All required files found!")
    return True

def main():
    """Run all tests"""
    print("🧪 Running Tests for Personal Todo Assistant")
    print("=" * 50)
    
    tests = [
        ("File Structure", check_file_structure),
        ("Imports", test_imports),
        ("Memory Manager", test_memory_manager),
        ("Todo Tools", test_todo_tools),
        ("API Key", test_api_key)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔍 Running {test_name} test...")
        if test_func():
            passed += 1
            print(f"✅ {test_name} test passed")
        else:
            print(f"❌ {test_name} test failed")
    
    print("\n" + "=" * 50)
    print(f"Test Results: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 All tests passed! Your setup is ready.")
        print("Run: python main.py")
    else:
        print("❌ Some tests failed. Please check the errors above.")
        
        print("\n🔧 Troubleshooting Steps:")
        print("1. Make sure you have all required files:")
        print("   - memory_manager.py")
        print("   - tools.py")
        print("   - .env")
        print("2. Install dependencies: pip install -r requirements.txt")
        print("3. Check that all files are in the same directory")
        print("4. Verify your Python version is 3.8+")
        print("5. Set up your Google API key in .env file")
        
        # Show current directory contents
        print(f"\n📂 Current directory: {os.getcwd()}")
        print("📄 Files in current directory:")
        for file in os.listdir("."):
            if os.path.isfile(file):
                print(f"   - {file}")

if __name__ == "__main__":
    main()