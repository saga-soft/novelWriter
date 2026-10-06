import os
os.chdir("/home/ab/workspaces/novelWriter")
with open("novelwriter/guimain.py", "r") as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    if line.startswith("        self.sideBar.tbAI.setVisible"):
        new_lines.append("        self.sideBar.tbAI.setVisible(CONFIG.aiEnabled)\n")
    else:
        new_lines.append(line)

with open("novelwriter/guimain.py", "w") as f:
    f.writelines(new_lines)

