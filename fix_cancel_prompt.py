import os

with open("novelwriter/gui/ai_assistant.py", "r") as f:
    content = f.read()

# Make sure cancelPrompt is defined before connecting, wait, PyQt connect works with unbound methods, but we must make sure the class method is indented properly.
