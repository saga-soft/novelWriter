import os

os.chdir("/home/ab/workspaces/novelWriter")
with open("novelwriter/guimain.py", "r") as f:
    content = f.read()

# 1. Import AiAssistantDock
import_str = "from novelwriter.gui.sidebar import GuiSideBar"
import_replacement = import_str + "\nfrom novelwriter.gui.ai_assistant import AiAssistantDock"
content = content.replace(import_str, import_replacement)

# 2. Add AI Assistant to UI layout
init_split_str = 'self.splitMain = QSplitter(Qt.Orientation.Horizontal)'
ai_pane_str = """
        self.aiAssistantPane = AiAssistantDock(self)
        self.aiAssistantPane.setVisible(False)
"""
content = content.replace(init_split_str, ai_pane_str + '\n        ' + init_split_str)

# 3. Add to splitMain
add_split_str = 'self.splitMain.addWidget(self.splitDocs)'
add_ai_split_str = add_split_str + '\n        self.splitMain.addWidget(self.aiAssistantPane)'
content = content.replace(add_split_str, add_ai_split_str)

# 4. Handle _changeView
change_view_str = 'elif view == nwView.STORY:\n            self.mainStack.setCurrentWidget(self.storyView)\n            self.storyView.viewStory()'
change_view_ai_str = change_view_str + '\n        elif view == nwView.AI:\n            is_visible = not self.aiAssistantPane.isVisible()\n            self.aiAssistantPane.setVisible(is_visible)\n            if is_visible:\n                self.aiAssistantPane.startServer()'
content = content.replace(change_view_str, change_view_ai_str)

with open("novelwriter/guimain.py", "w") as f:
    f.write(content)

print("Success")
