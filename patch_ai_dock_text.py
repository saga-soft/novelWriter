import os
os.chdir("/home/ab/workspaces/novelWriter")
with open("novelwriter/gui/ai_assistant.py", "r") as f:
    content = f.read()

content = content.replace("text = self.mainGui.docEditor.getPlainText()", "text = self.mainGui.docEditor.getText()")

with open("novelwriter/gui/ai_assistant.py", "w") as f:
    f.write(content)
