import os
os.chdir("/home/ab/workspaces/novelWriter")
with open("novelwriter/dialogs/preferences.py", "r") as f:
    content = f.read()

prompt_old = """        # System Prompt
        self.aiSystemPrompt = QTextEdit(self)
        self.aiSystemPrompt.setFixedHeight(80)
        self.aiSystemPrompt.setPlainText(CONFIG.aiSystemPrompt)
        self.mainForm.addRow(
            self.tr("System Specialization"),
            self.aiSystemPrompt,
            self.tr("Pre-prompt to define the assistant's behavior/role."),
        )"""

prompt_new = """        # Co-author
        self.aiPromptCoAuthor = QTextEdit(self)
        self.aiPromptCoAuthor.setFixedHeight(60)
        self.aiPromptCoAuthor.setPlainText(CONFIG.aiPromptCoAuthor)
        self.mainForm.addRow(self.tr("Co-author Role"), self.aiPromptCoAuthor, self.tr("Prompt for the Co-author specialization."))
        
        # Editor
        self.aiPromptEditor = QTextEdit(self)
        self.aiPromptEditor.setFixedHeight(60)
        self.aiPromptEditor.setPlainText(CONFIG.aiPromptEditor)
        self.mainForm.addRow(self.tr("Editor Role"), self.aiPromptEditor, self.tr("Prompt for the Editor specialization."))
        
        # Publisher
        self.aiPromptPublisher = QTextEdit(self)
        self.aiPromptPublisher.setFixedHeight(60)
        self.aiPromptPublisher.setPlainText(CONFIG.aiPromptPublisher)
        self.mainForm.addRow(self.tr("Publisher Role"), self.aiPromptPublisher, self.tr("Prompt for the Publisher specialization."))
        
        # Reader
        self.aiPromptReader = QTextEdit(self)
        self.aiPromptReader.setFixedHeight(60)
        self.aiPromptReader.setPlainText(CONFIG.aiPromptReader)
        self.mainForm.addRow(self.tr("Reader Role"), self.aiPromptReader, self.tr("Prompt for the Reader specialization."))"""

content = content.replace(prompt_old, prompt_new)

save_old = 'CONFIG.aiSystemPrompt = self.aiSystemPrompt.toPlainText().strip()'
save_new = '''CONFIG.aiPromptCoAuthor = self.aiPromptCoAuthor.toPlainText().strip()
        CONFIG.aiPromptEditor = self.aiPromptEditor.toPlainText().strip()
        CONFIG.aiPromptPublisher = self.aiPromptPublisher.toPlainText().strip()
        CONFIG.aiPromptReader = self.aiPromptReader.toPlainText().strip()'''

content = content.replace(save_old, save_new)

with open("novelwriter/dialogs/preferences.py", "w") as f:
    f.write(content)

