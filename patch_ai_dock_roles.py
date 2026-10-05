import os
os.chdir("/home/ab/workspaces/novelWriter")
with open("novelwriter/gui/ai_assistant.py", "r") as f:
    content = f.read()

# Add QComboBox to imports
content = content.replace(
    'QTextEdit, QPushButton, QLabel, QMessageBox',
    'QTextEdit, QPushButton, QLabel, QMessageBox, QComboBox'
)

# Add Role layout to AiAssistantDock UI
ui_old = '''        self.headerLayout.addWidget(self.titleLabel)
        self.headerLayout.addStretch()
        self.layout.addLayout(self.headerLayout)
        
        # Chat History'''
ui_new = '''        self.headerLayout.addWidget(self.titleLabel)
        self.headerLayout.addStretch()
        self.layout.addLayout(self.headerLayout)
        
        # Role Selector
        self.roleLayout = QHBoxLayout()
        self.roleLayout.addWidget(QLabel("Active Role:", self))
        self.roleCombo = QComboBox(self)
        self.roleCombo.addItems(["Co-author", "Editor", "Publisher", "Reader"])
        self.roleCombo.setCurrentText(getattr(CONFIG, "aiActiveRole", "Co-author"))
        self.roleCombo.currentTextChanged.connect(self.changeRole)
        self.roleLayout.addWidget(self.roleCombo)
        self.roleLayout.addStretch()
        self.layout.addLayout(self.roleLayout)
        
        # Chat History'''
content = content.replace(ui_old, ui_new)

# Add changeRole method and update getActiveContext
methods_old = '''    def getActiveContext(self):
        text = self.mainGui.docEditor.getPlainText()
        context_size = getattr(CONFIG, 'aiContextSize', 8192)
        max_chars = int((context_size - 1000) * 3)
        if len(text) > max_chars:
            text = "... " + text[-max_chars:]
        return f"{getattr(CONFIG, 'aiSystemPrompt', '')}\\n\\nHere is the current text the author is working on:\\n\\n---\\n{text}\\n---\\n\\nAssist the author as requested."'''

methods_new = '''    def changeRole(self, role_name: str):
        CONFIG.aiActiveRole = role_name
        CONFIG.saveConfig()

    def getActiveContext(self):
        text = self.mainGui.docEditor.getPlainText()
        context_size = getattr(CONFIG, 'aiContextSize', 8192)
        max_chars = int((context_size - 1000) * 3)
        if len(text) > max_chars:
            text = "... " + text[-max_chars:]
            
        role = self.roleCombo.currentText()
        if role == "Co-author":
            sys_prompt = getattr(CONFIG, 'aiPromptCoAuthor', '')
        elif role == "Editor":
            sys_prompt = getattr(CONFIG, 'aiPromptEditor', '')
        elif role == "Publisher":
            sys_prompt = getattr(CONFIG, 'aiPromptPublisher', '')
        else:
            sys_prompt = getattr(CONFIG, 'aiPromptReader', '')
            
        return f"{sys_prompt}\\n\\nHere is the current text the author is working on:\\n\\n---\\n{text}\\n---\\n\\nAssist the author as requested."'''
content = content.replace(methods_old, methods_new)

with open("novelwriter/gui/ai_assistant.py", "w") as f:
    f.write(content)
