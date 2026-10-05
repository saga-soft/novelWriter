import os
os.chdir("/home/ab/workspaces/novelWriter")
with open("novelwriter/gui/sidebar.py", "r") as f:
    content = f.read()

content = content.replace("nwView.AI))\\n        self.tbAI.setVisible(CONFIG.aiEnabled)", "nwView.AI))\n        self.tbAI.setVisible(CONFIG.aiEnabled)")

with open("novelwriter/gui/sidebar.py", "w") as f:
    f.write(content)
