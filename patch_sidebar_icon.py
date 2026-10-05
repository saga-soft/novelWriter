import os
os.chdir("/home/ab/workspaces/novelWriter")
with open("novelwriter/gui/sidebar.py", "r") as f:
    content = f.read()

# Change NFlatIconButton to standard QPushButton or just fix NFlatIconButton
# Actually we can just do:
content = content.replace('self.tbAI = NFlatIconButton(self, iSz, "", 0.25)', 
'''from PyQt6.QtCore import Qt
        self.tbAI = NFlatIconButton(self, iSz, "settings:sidebar", 0.25)
        self.tbAI.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)''')

with open("novelwriter/gui/sidebar.py", "w") as f:
    f.write(content)
