import os

os.chdir("/home/ab/workspaces/novelWriter")

# --- 1. Fix AiWorker to accept messages list ---
with open("novelwriter/gui/ai_assistant.py", "r") as f:
    ai_dock = f.read()

# Replace AiWorker __init__ and run
worker_old = '''    def __init__(self, system_prompt: str, user_prompt: str):
        super().__init__()
        self.system_prompt = system_prompt
        self.user_prompt = user_prompt
        self._is_running = True

    def stop(self):
        self._is_running = False

    def run(self):
        base_url = CONFIG.aiEndpoint.rstrip('/') if hasattr(CONFIG, 'aiEndpoint') and CONFIG.aiEndpoint else "http://127.0.0.1:8080"
        url = f"{base_url}/chat/completions" if base_url.endswith("/v1") else f"{base_url}/v1/chat/completions"
        headers = {"Content-Type": "application/json"}
        payload = {
            "model": getattr(CONFIG, 'aiModel', ''),
            "messages": [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": self.user_prompt}
            ],
            "temperature": getattr(CONFIG, 'aiTemperature', 0.7),
            "stream": True
        }'''

worker_new = '''    def __init__(self, messages: list):
        super().__init__()
        self.messages = messages
        self._is_running = True

    def stop(self):
        self._is_running = False

    def run(self):
        base_url = CONFIG.aiEndpoint.rstrip('/') if hasattr(CONFIG, 'aiEndpoint') and CONFIG.aiEndpoint else "http://127.0.0.1:8080"
        url = f"{base_url}/chat/completions" if base_url.endswith("/v1") else f"{base_url}/v1/chat/completions"
        headers = {"Content-Type": "application/json"}
        payload = {
            "model": getattr(CONFIG, 'aiModel', ''),
            "messages": self.messages,
            "temperature": getattr(CONFIG, 'aiTemperature', 0.7),
            "stream": True
        }'''
ai_dock = ai_dock.replace(worker_old, worker_new)


# --- 2. Add message_history, timer, clear button, and speed tracking ---
# Add `import time` at the top
ai_dock = ai_dock.replace('import json', 'import json\nimport time')

init_old = '''        self.worker = None
        self.prompt_tokens = 0
        self.completion_tokens = 0
        self.is_thinking = False'''
init_new = '''        self.worker = None
        self.prompt_tokens = 0
        self.completion_tokens = 0
        self.is_thinking = False
        self.message_history = []
        self.first_token_time = 0
        self.current_response = ""'''
ai_dock = ai_dock.replace(init_old, init_new)

# Add clear button next to cancel
status_layout_old = '''        self.cancelBtn = QPushButton("Cancel", self)
        self.cancelBtn.setEnabled(False)
        self.cancelBtn.clicked.connect(self.cancelPrompt)

        self.statusLayout.addWidget(self.statusLabel, 1)
        self.statusLayout.addWidget(self.cancelBtn)
        self.layout.addLayout(self.statusLayout)'''
status_layout_new = '''        self.cancelBtn = QPushButton("Cancel", self)
        self.cancelBtn.setEnabled(False)
        self.cancelBtn.clicked.connect(self.cancelPrompt)
        
        self.clearBtn = QPushButton("Clear", self)
        self.clearBtn.clicked.connect(self.clearChat)

        self.statusLayout.addWidget(self.statusLabel, 1)
        self.statusLayout.addWidget(self.cancelBtn)
        self.statusLayout.addWidget(self.clearBtn)
        self.layout.addLayout(self.statusLayout)'''
ai_dock = ai_dock.replace(status_layout_old, status_layout_new)


# Add clearChat method
clear_method = '''    def clearChat(self):
        self.message_history = []
        self.chatBrowser.clear()
        self.chatBrowser.append("<b>System:</b> Chat cleared. Ready for new prompt.")
        self.statusLabel.setText("Ready.")

    def changeRole(self, role_name: str):'''
ai_dock = ai_dock.replace('    def changeRole(self, role_name: str):', clear_method)


# Update sendPrompt
send_old = '''        self.inputEdit.clear()
        self.sendBtn.setEnabled(False)
        self.cancelBtn.setEnabled(True)

        self.chatBrowser.append(f"<br><b>You:</b> {prompt}<br><b>AI:</b> ")

        system_prompt = self.getActiveContext()
        
        self.prompt_tokens = len(system_prompt + prompt) // 4
        self.completion_tokens = 0
        self.is_thinking = True
        self.statusLabel.setText(f"Thinking... (Prompt Tokens: ~{self.prompt_tokens})")

        self.worker = AiWorker(system_prompt, prompt)'''
send_new = '''        self.inputEdit.clear()
        self.sendBtn.setEnabled(False)
        self.cancelBtn.setEnabled(True)
        self.clearBtn.setEnabled(False)

        self.chatBrowser.append(f"<br><b>You:</b> {prompt}<br><b>AI:</b> ")

        system_prompt = self.getActiveContext()
        
        self.message_history.append({"role": "user", "content": prompt})
        
        messages = [{"role": "system", "content": system_prompt}] + self.message_history
        
        # Estimate prompt tokens
        history_text = " ".join([m["content"] for m in self.message_history])
        self.prompt_tokens = len(system_prompt + history_text) // 4
        self.completion_tokens = 0
        self.current_response = ""
        self.is_thinking = True
        self.first_token_time = 0
        self.statusLabel.setText(f"Thinking... (Prompt Tokens: ~{self.prompt_tokens})")

        self.worker = AiWorker(messages)'''
ai_dock = ai_dock.replace(send_old, send_new)

# Update onNewToken for speed tracking
token_old = '''    def onNewToken(self, token: str):
        self.completion_tokens += 1
        if self.is_thinking:
            self.is_thinking = False

        if self.completion_tokens % 3 == 0 or self.completion_tokens == 1:
            self.statusLabel.setText(f"Generating... (Prompt: ~{self.prompt_tokens} | Output: ~{self.completion_tokens})")

        cursor = self.chatBrowser.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.chatBrowser.setTextCursor(cursor)
        self.chatBrowser.insertPlainText(token)'''
token_new = '''    def onNewToken(self, token: str):
        self.completion_tokens += 1
        self.current_response += token
        if self.is_thinking:
            self.is_thinking = False
            self.first_token_time = time.time()
            
        elapsed = time.time() - self.first_token_time
        tps = self.completion_tokens / elapsed if elapsed > 0 else 0

        if self.completion_tokens % 3 == 0 or self.completion_tokens == 1:
            self.statusLabel.setText(f"Generating... (Prompt: ~{self.prompt_tokens} | Output: ~{self.completion_tokens} | Speed: {tps:.1f} t/s)")

        cursor = self.chatBrowser.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.chatBrowser.setTextCursor(cursor)
        self.chatBrowser.insertPlainText(token)'''
ai_dock = ai_dock.replace(token_old, token_new)


# Update onGenerationFinished & Error & Cancel to re-enable clearBtn and append to history
finish_old = '''    def onGenerationFinished(self, response: str):
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
finish_new = '''    def onGenerationFinished(self, response: str):
        self.sendBtn.setEnabled(True)
        self.cancelBtn.setEnabled(False)
        self.clearBtn.setEnabled(True)
        elapsed = time.time() - self.first_token_time if self.first_token_time else 0
        tps = self.completion_tokens / elapsed if elapsed > 0 else 0
        self.statusLabel.setText(f"Finished. (Prompt: ~{self.prompt_tokens} | Output: ~{self.completion_tokens} | Speed: {tps:.1f} t/s)")
        self.chatBrowser.append("<br>")
        self.message_history.append({"role": "assistant", "content": self.current_response})

    def onGenerationError(self, error: str):
        self.sendBtn.setEnabled(True)
        self.cancelBtn.setEnabled(False)
        self.clearBtn.setEnabled(True)
        self.statusLabel.setText("Error occurred.")
        self.chatBrowser.append(f"<br><b>Error:</b> {error}<br>")
        
    def cancelPrompt(self):
        if self.worker:
            self.worker.stop()
        self.sendBtn.setEnabled(True)
        self.cancelBtn.setEnabled(False)
        self.clearBtn.setEnabled(True)
        self.statusLabel.setText(f"Cancelled. (Prompt: ~{self.prompt_tokens} | Output: ~{self.completion_tokens})")
        self.chatBrowser.append("<br><i>[Generation Cancelled]</i><br>")
        if self.current_response:
            self.message_history.append({"role": "assistant", "content": self.current_response})'''
ai_dock = ai_dock.replace(finish_old, finish_new)


with open("novelwriter/gui/ai_assistant.py", "w") as f:
    f.write(ai_dock)


# --- 3. Fix Guimain Splitter resizing ---
with open("novelwriter/guimain.py", "r") as f:
    guimain = f.read()

guimain_old = '''        self.splitMain.addWidget(self.aiAssistantPane)
        self.splitMain.setOpaqueResize(False)
        self.splitMain.setHandleWidth(4)
        self.splitMain.setSizes([max(s, 100) for s in CONFIG.mainPanePos])
        self.splitMain.setCollapsible(0, False)
        self.splitMain.setCollapsible(1, False)
        self.splitMain.setStretchFactor(0, 0)
        self.splitMain.setStretchFactor(1, 1)'''
guimain_new = '''        self.splitMain.addWidget(self.aiAssistantPane)
        self.aiAssistantPane.setMinimumWidth(250)
        self.splitMain.setOpaqueResize(False)
        self.splitMain.setHandleWidth(4)
        
        # Ensure sizes config handles 3 elements
        sizes = [max(s, 100) for s in CONFIG.mainPanePos]
        if len(sizes) == 2:
            sizes.append(0)  # Hidden AI pane size
        self.splitMain.setSizes(sizes)
        
        self.splitMain.setCollapsible(0, False)
        self.splitMain.setCollapsible(1, False)
        self.splitMain.setCollapsible(2, False)
        self.splitMain.setStretchFactor(0, 0)
        self.splitMain.setStretchFactor(1, 1)
        self.splitMain.setStretchFactor(2, 0)'''
guimain = guimain.replace(guimain_old, guimain_new)

with open("novelwriter/guimain.py", "w") as f:
    f.write(guimain)

print("Updates applied successfully.")
