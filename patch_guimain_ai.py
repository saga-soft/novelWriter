import os

os.chdir("/home/ab/workspaces/novelWriter")
with open("novelwriter/guimain.py", "r") as f:
    content = f.read()

# Add a check to _processConfigChanges
insert_idx = content.find("        if not update.editor:")
ai_toggle = "        self.sideBar.tbAI.setVisible(CONFIG.aiEnabled)\\n"
content = content[:insert_idx] + ai_toggle + content[insert_idx:]

with open("novelwriter/guimain.py", "w") as f:
    f.write(content)

with open("novelwriter/gui/sidebar.py", "r") as f:
    content = f.read()

content = content.replace("        self.tbAI.clicked.connect(qtWeakLambda(self._emitViewChange, nwView.AI))", "        self.tbAI.clicked.connect(qtWeakLambda(self._emitViewChange, nwView.AI))\\n        self.tbAI.setVisible(CONFIG.aiEnabled)")

with open("novelwriter/gui/sidebar.py", "w") as f:
    f.write(content)

print("Guimain AI visibility patched.")
