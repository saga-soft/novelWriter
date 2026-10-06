import os
os.chdir("/home/ab/workspaces/novelWriter")
with open("novelwriter/gui/ai_assistant.py", "r") as f:
    content = f.read()

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
