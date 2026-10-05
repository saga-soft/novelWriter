import os
os.chdir("/home/ab/workspaces/novelWriter")
with open("novelwriter/gui/sidebar.py", "r") as f:
    content = f.read()

content = content.replace('self.tbAI = NFlatIconButton(self, iSz, "settings:sidebar", 0.25)', 'self.tbAI = NFlatIconButton(self, iSz, "ai_assistant:sidebar", 0.25)')
content = content.replace('self.tbAI.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)', '# self.tbAI.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)')

with open("novelwriter/gui/sidebar.py", "w") as f:
    f.write(content)
