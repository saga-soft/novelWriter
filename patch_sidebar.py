import os

os.chdir("/home/ab/workspaces/novelWriter")
with open("novelwriter/gui/sidebar.py", "r") as f:
    content = f.read()

# Add AI button
story_btn_str = 'self.tbStory.clicked.connect(qtWeakLambda(self._emitViewChange, nwView.STORY))'
ai_btn_str = story_btn_str + """

        self.tbAI = NFlatIconButton(self, iSz, "", 0.25)
        self.tbAI.setText("AI")
        self.tbAI.setToolTip(self.tr("Toggle AI Assistant"))
        self.tbAI.clicked.connect(qtWeakLambda(self._emitViewChange, nwView.AI))
"""
content = content.replace(story_btn_str, ai_btn_str)

# Add AI button to the layout
# We need to find where buttons are added.
# In sidebar.py, there's `self.layout = QVBoxLayout(self)`? Let's check how they are laid out.
