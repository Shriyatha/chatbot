#!/usr/bin/env python3
"""
Setup script for the Personal Todo Assistant
"""

import os
import sys
import subprocess

def install_requirements():
    """Install required packages"""
    print("Installing required packages...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Requirements installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing requirements: {e}")
        return False

def setup_env_file():
    """Setup environment file"""
    if not os.path.exists(".env"):
        if os.path.exists(".env.template"):
            print("Creating .env file from template...")
            with open(".env.template", "r") as template:
                with open(".env", "w") as env_file:
                    env_file.write(template.read())
            print("✅ .env file created! Please edit it with your Google API key.")
        else:
            print("Creating .env file...")
            with open(".env", "w") as env_file:
                env_file.write("# Google AI Studio API Key\n")
                env_file.write("# Get your free API key from: https://aistudio.google.com/app/apikey\n")
                env_file.write("GOOGLE_API_KEY=your_google_api_key_here\n")
            print("✅ .env file created! Please edit it with your Google API key.")
    else:
        print("✅ .env file already exists!")

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required!")
        return False
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro} detected")
    return True

def main():
    """Main setup function"""
    print("🚀 Setting up Personal Todo Assistant...")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Install requirements
    if not install_requirements():
        sys.exit(1)
    
    # Setup environment file
    setup_env_file()
    
    # Create data directory
    if not os.path.exists("user_data"):
        os.makedirs("user_data")
        print("✅ Data directory created!")
    
    print("\n" + "=" * 50)
    print("🎉 Setup complete!")
    print("\nNext steps:")
    print("1. Get your free Google API key from: https://aistudio.google.com/app/apikey")
    print("2. Edit the .env file and add your API key")
    print("3. Run: python main.py")
    print("\nEnjoy your personal todo assistant! 🤖")

if __name__ == "__main__":
    main()