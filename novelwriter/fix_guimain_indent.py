import os
os.chdir("/home/ab/workspaces/novelWriter")
with open("novelwriter/guimain.py", "r") as f:
    lines = f.readlines()

new_lines = []
skip = False
for i, line in enumerate(lines):
    if line.strip() == "self.sideBar.tbAI.setVisible(CONFIG.aiEnabled)":
        continue
    if line.strip() == "if not update.editor:" and lines[i+1].strip() == "self.docEditor.initViewport()":
        new_lines.append("        self.sideBar.tbAI.setVisible(CONFIG.aiEnabled)\n")
        new_lines.append("            if not update.editor:\n")
        continue
    if line.strip() == "if not update.editor:" and "self.docEditor.initViewport()" not in lines[i+1]:
        # we might have messed up the indentation of the previous one
        pass
    
    new_lines.append(line)

with open("novelwriter/guimain.py", "w") as f:
    f.writelines(new_lines)

