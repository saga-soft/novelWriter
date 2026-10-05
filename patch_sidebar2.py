import os

os.chdir("/home/ab/workspaces/novelWriter")
with open("novelwriter/gui/sidebar.py", "r") as f:
    content = f.read()

# Add to outerBox
build_str = 'self.outerBox.addWidget(self.tbBuild)'
ai_add_str = build_str + '\n        self.outerBox.addWidget(self.tbAI)'
content = content.replace(build_str, ai_add_str)

with open("novelwriter/gui/sidebar.py", "w") as f:
    f.write(content)

print("Success")
