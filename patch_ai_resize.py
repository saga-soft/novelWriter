import os
os.chdir("/home/ab/workspaces/novelWriter")
with open("novelwriter/guimain.py", "r") as f:
    content = f.read()

old_ai = '''        elif view == nwView.AI:
            is_visible = not self.aiAssistantPane.isVisible()
            self.aiAssistantPane.setVisible(is_visible)

        else:  # pragma: no cover'''

new_ai = '''        elif view == nwView.AI:
            is_visible = not self.aiAssistantPane.isVisible()
            self.aiAssistantPane.setVisible(is_visible)
            if is_visible:
                sizes = self.splitMain.sizes()
                total = sum(sizes)
                if total > 0 and len(sizes) >= 3:
                    ai_width = int(total * 0.2)
                    sizes[1] = max(100, sizes[1] - ai_width + sizes[2])
                    sizes[2] = ai_width
                    self.splitMain.setSizes(sizes)

        else:  # pragma: no cover'''

content = content.replace(old_ai, new_ai)

with open("novelwriter/guimain.py", "w") as f:
    f.write(content)
