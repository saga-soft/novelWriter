import os
os.chdir("/home/ab/workspaces/novelWriter")
with open("novelwriter/gui/sidebar.py", "r") as f:
    content = f.read()

content = content.replace("self.tbSettings.refreshTheme()\\n            self.tbAI.setVisible(CONFIG.aiEnabled)", "self.tbSettings.refreshTheme()\n            self.tbAI.setVisible(CONFIG.aiEnabled)")

with open("novelwriter/gui/sidebar.py", "w") as f:
    f.write(content)
