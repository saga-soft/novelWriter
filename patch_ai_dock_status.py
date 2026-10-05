import os

with open("novelwriter/gui/ai_assistant.py", "r") as f:
    content = f.read()

# 1. Update init to add new variables
init_old = '''        self.worker = None

        logger.debug("Create: AiAssistantDock")'''
init_new = '''        self.worker = None
        self.prompt_tokens = 0
        self.completion_tokens = 0
        self.is_thinking = False

        logger.debug("Create: AiAssistantDock")'''
content = content.replace(init_old, init_new)

# 2. Add Status and Cancel Area
layout_old = '''        # Chat History
        self.chatBrowser = QTextBrowser(self)
        self.chatBrowser.setOpenExternalLinks(True)
        self.layout.addWidget(self.chatBrowser, 1)

        # Input Area'''
layout_new = '''        # Chat History
        self.chatBrowser = QTextBrowser(self)
        self.chatBrowser.setOpenExternalLinks(True)
        self.layout.addWidget(self.chatBrowser, 1)

        # Status & Cancel Area
        self.statusLayout = QHBoxLayout()
        self.statusLabel = QLabel("Ready.", self)
        font = self.statusLabel.font()
        font.setPointSize(max(8, font.pointSize() - 1))
        self.statusLabel.setFont(font)
        
        self.cancelBtn = QPushButton("Cancel", self)
        self.cancelBtn.setEnabled(False)
        self.cancelBtn.clicked.connect(self.cancelPrompt)
        
        self.statusLayout.addWidget(self.statusLabel, 1)
        self.statusLayout.addWidget(self.cancelBtn)
        self.layout.addLayout(self.statusLayout)

        # Input Area'''
content = content.replace(layout_old, layout_new)

# 3. Update sendPrompt
send_old = '''        self.inputEdit.clear()
        self.sendBtn.setEnabled(False)

        self.chatBrowser.append(f"<br><b>You:</b> {prompt}<br><b>AI:</b> ")

        system_prompt = self.getActiveContext()

        self.worker = AiWorker(system_prompt, prompt)'''
send_new = '''        self.inputEdit.clear()
        self.sendBtn.setEnabled(False)
        self.cancelBtn.setEnabled(True)

        self.chatBrowser.append(f"<br><b>You:</b> {prompt}<br><b>AI:</b> ")

        system_prompt = self.getActiveContext()
        
        self.prompt_tokens = len(system_prompt + prompt) // 4
        self.completion_tokens = 0
        self.is_thinking = True
        self.statusLabel.setText(f"Thinking... (Prompt Tokens: ~{self.prompt_tokens})")

        self.worker = AiWorker(system_prompt, prompt)'''
content = content.replace(send_old, send_new)

# 4. Update onNewToken
token_old = '''    def onNewToken(self, token: str):
        cursor = self.chatBrowser.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.chatBrowser.setTextCursor(cursor)
        self.chatBrowser.insertPlainText(token)'''
token_new = '''    def onNewToken(self, token: str):
        self.completion_tokens += 1
        if self.is_thinking:
            self.is_thinking = False
        
        if self.completion_tokens % 3 == 0 or self.completion_tokens == 1:
            self.statusLabel.setText(f"Generating... (Prompt: ~{self.prompt_tokens} | Output: ~{self.completion_tokens})")
            
        cursor = self.chatBrowser.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.chatBrowser.setTextCursor(cursor)
        self.chatBrowser.insertPlainText(token)'''
content = content.replace(token_old, token_new)

# 5. Update onGenerationFinished & Error, add cancelPrompt
finish_old = '''    def onGenerationFinished(self, response: str):
        self.sendBtn.setEnabled(True)
        self.chatBrowser.append("<br>")

    def onGenerationError(self, error: str):
        self.sendBtn.setEnabled(True)
        self.chatBrowser.append(f"<br><b>Error:</b> {error}<br>")'''
finish_new = '''    def onGenerationFinished(self, response: str):
        self.sendBtn.setEnabled(True)
        self.cancelBtn.setEnabled(False)
        self.statusLabel.setText(f"Finished. (Prompt: ~{self.prompt_tokens} | Output: ~{self.completion_tokens})")
        self.chatBrowser.append("<br>")

    def onGenerationError(self, error: str):
        self.sendBtn.setEnabled(True)
        self.cancelBtn.setEnabled(False)
        self.statusLabel.setText("Error occurred.")
        self.chatBrowser.append(f"<br><b>Error:</b> {error}<br>")

    def cancelPrompt(self):
        if self.worker:
            self.worker.stop()
        self.sendBtn.setEnabled(True)
        self.cancelBtn.setEnabled(False)
        self.statusLabel.setText(f"Cancelled. (Prompt: ~{self.prompt_tokens} | Output: ~{self.completion_tokens})")
        self.chatBrowser.append("<br><i>[Generation Cancelled]</i><br>")'''
content = content.replace(finish_old, finish_new)

with open("novelwriter/gui/ai_assistant.py", "w") as f:
    f.write(content)

print("Status and Cancel applied!")
