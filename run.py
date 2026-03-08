import subprocess
import time
import sys
import os
import webbrowser

def install_dependencies():
    print("Checking dependencies...")
    
    # Identify the correct python/pip to use
    venv_pip = os.path.join(".venv", "Scripts", "pip.exe")
    venv_python = os.path.join(".venv", "Scripts", "python.exe")
    
    if os.path.exists(venv_pip):
        print("Using virtual environment .venv...")
        pip_cmd = [venv_pip, "install", "-r", "requirements.txt"]
        python_cmd = venv_python
    else:
        pip_cmd = [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"]
        python_cmd = sys.executable

    try:
        print(f"Installing dependencies using: {' '.join(pip_cmd)}")
        subprocess.check_call(pip_cmd)
        return python_cmd
    except Exception as e:
        print(f"Error installing dependencies: {e}")
        return sys.executable

def main():
    # Install dependencies first and get the correct python path
    python_executable = install_dependencies()

    print("Starting MouDF Server...")
    # Start the Flask app using the correct python version
    process = subprocess.Popen([python_executable, "app.py"])

    # Wait for the server to start
    time.sleep(2)

    # Open the browser
    url = "http://127.0.0.1:5000"
    print(f"Opening MouDF at {url}...")
    
    # Try to open in Chrome specifically if possible, else default browser
    try:
        # Common paths for Chrome on Windows
        chrome_paths = [
            "C:/Program Files/Google/Chrome/Application/chrome.exe",
            "C:/Program Files (x86)/Google/Chrome/Application/chrome.exe"
        ]
        
        chrome_opened = False
        for path in chrome_paths:
            if os.path.exists(path):
                subprocess.Popen([path, url])
                chrome_opened = True
                break
        
        if not chrome_opened:
            webbrowser.open(url)
    except Exception:
        webbrowser.open(url)

    try:
        print("\nMouDF is running! Press Ctrl+C to stop the server.")
        process.wait()
    except KeyboardInterrupt:
        print("\nStopping MouDF...")
        process.terminate()

if __name__ == "__main__":
    main()
