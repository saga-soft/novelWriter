import os
os.chdir("/home/ab/workspaces/novelWriter")
with open("novelwriter/guimain.py", "r") as f:
    content = f.read()

content = content.replace("        if update.viewport:\n        self.sideBar.tbAI.setVisible(CONFIG.aiEnabled)\n            if not update.editor:", "        self.sideBar.tbAI.setVisible(CONFIG.aiEnabled)\n        if update.viewport:\n            if not update.editor:")

with open("novelwriter/guimain.py", "w") as f:
    f.write(content)
