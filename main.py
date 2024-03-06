from flask import Flask, render_template, request

from pynput import keyboard
from pynput.keyboard import Key, Controller
import pyperclip
import time
import httpx
from string import Template

app = Flask(__name__)

controller = Controller()

OLLAMA_ENDPOINT = "http://localhost:11434/api/generate" 
OLLAMA_CONFIG = {"model": "mistral", 
                 "keep_alive":"5m", 
                 "stream": False
                 }

# Allows to define a template where we will later insert the text
PROMPT_TEMPLATE = Template(
    """Fix all typos and casing and punctuation in this text, but preserve all new line characters. Keep the same language.

$text

Return only the corrected text, don't include a preamble.
"""
    )

def fix_text(text):
    prompt = PROMPT_TEMPLATE.substitute(text=text)
    try:
        response = httpx.post(
            OLLAMA_ENDPOINT,
            json={"prompt": prompt, **OLLAMA_CONFIG},
            headers={"Content-Type": "application/json"},
            timeout=20,  
        )
        response.raise_for_status()  
        return response.json()["response"].strip()
    except httpx.HTTPStatusError as e:
        print(f"HTTP error: {e}")
    except httpx.RequestError as e:
        print(f"Request error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    return None


def fix_current_line():
    # Select the current line
    controller.press(Key.cmd)
    controller.press(Key.shift)
    controller.press(Key.left)
    
    # Release the keys
    controller.release(Key.cmd)
    controller.release(Key.shift)
    controller.release(Key.left)
    
    # Calls fix_selection function
    fix_selection()

def fix_selection():
    # First I copy the clipboard
    with controller.pressed(Key.cmd):
        controller.tap("c")
        
    # Then we get the text from the clipboard
    time.sleep(0.1)
    text = pyperclip.paste()
    print("Original text:", text)  # Add this line to check the original text
    
    # I fix the text
    fixed_text = fix_text(text)
    print("Fixed text:", fixed_text)  # Add this line to check the fixed text
    
    if fixed_text is not None:  # Check if the text was fixed successfully
        # I copy back the text to the clipboard
        pyperclip.copy(fixed_text)
        time.sleep(0.1)
        
        # Paste back fixed text
        with controller.pressed(Key.cmd):
            controller.tap("v")
    else:
        print("Failed to fix the text.")
    
def on_f9():
    fix_current_line()

def on_f10():
    fix_selection()


@app.route('/', methods=['GET', 'POST'])
def index():
    fixed_text = None
    if request.method == 'POST':
        text = request.form['text']
        pyperclip.copy(text)  # Copy the text to the clipboard
        fix_current_line()  # Call the function to fix the current line
        fixed_text = pyperclip.paste()
    return render_template('index.html', fixed_text=fixed_text)

if __name__ == '__main__':
    app.run(debug=True)

with keyboard.GlobalHotKeys({
        "<101>": on_f9,
        "<109>": on_f10}) as h:
    h.join()