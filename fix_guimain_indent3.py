import os
os.chdir("/home/ab/workspaces/novelWriter")
with open("novelwriter/guimain.py", "r") as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if "self.sideBar.tbAI.setVisible" in line:
        lines[i] = "        self.sideBar.tbAI.setVisible(CONFIG.aiEnabled)\n"

with open("novelwriter/guimain.py", "w") as f:
    f.writelines(lines)
