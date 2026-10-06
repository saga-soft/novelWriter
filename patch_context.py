import os
with open("novelwriter/gui/ai_assistant.py", "r") as f:
    content = f.read()

old_ctx = """    def getActiveContext(self):
        text = self.mainGui.docEditor.getText()
        context_size = getattr(CONFIG, 'aiContextSize', 8192)
        max_chars = int((context_size - 1000) * 3)
        if len(text) > max_chars:
            text = "... " + text[-max_chars:]"""

new_ctx = """    def getActiveContext(self):
        text = self.mainGui.docEditor.getText()
        provider = getattr(CONFIG, 'aiProvider', 'Local / Llama.cpp')
        if provider == "Local / Llama.cpp":
            context_size = getattr(CONFIG, 'aiContextSize', 8192)
            max_chars = int((context_size - 1000) * 3)
            if len(text) > max_chars:
                text = "... " + text[-max_chars:]"""

content = content.replace(old_ctx, new_ctx)

with open("novelwriter/gui/ai_assistant.py", "w") as f:
    f.write(content)
print("Context patched.")
