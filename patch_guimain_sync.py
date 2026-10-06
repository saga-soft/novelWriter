import os

with open("novelwriter/guimain.py", "r") as f:
    content = f.read()

old_sync = """        self.sideBar.tbAI.setVisible(CONFIG.aiEnabled)
        if update.viewport:"""

new_sync = """        self.sideBar.tbAI.setVisible(CONFIG.aiEnabled)
        if hasattr(self.aiAssistantPane, "syncSettings"):
            self.aiAssistantPane.syncSettings()
        if update.viewport:"""

content = content.replace(old_sync, new_sync)

with open("novelwriter/guimain.py", "w") as f:
    f.write(content)

with open("novelwriter/gui/ai_assistant.py", "r") as f:
    content = f.read()

# Replace showEvent with syncSettings
old_show = """    def showEvent(self, event):
        super().showEvent(event)
        # Sync with preferences when shown
        provider = getattr(CONFIG, "aiProvider", "Local / Llama.cpp")
        if self.providerCombo.currentText() != provider:
            self.providerCombo.blockSignals(True)
            self.providerCombo.setCurrentText(provider)
            self.providerCombo.blockSignals(False)
            
        model = getattr(CONFIG, "aiModel", "")
        if model and self.modelCombo.currentText() != model:
            self.modelCombo.blockSignals(True)
            if self.modelCombo.findText(model) < 0:
                self.modelCombo.addItem(model)
            self.modelCombo.setCurrentText(model)
            self.modelCombo.blockSignals(False)

    def closeEvent(self, event):"""

new_sync_method = """    def syncSettings(self):
        provider = getattr(CONFIG, "aiProvider", "Local / Llama.cpp")
        if self.providerCombo.currentText() != provider:
            self.providerCombo.blockSignals(True)
            self.providerCombo.setCurrentText(provider)
            self.providerCombo.blockSignals(False)
            
        model = getattr(CONFIG, "aiModel", "")
        if model and self.modelCombo.currentText() != model:
            self.modelCombo.blockSignals(True)
            if self.modelCombo.findText(model) < 0:
                self.modelCombo.addItem(model)
            self.modelCombo.setCurrentText(model)
            self.modelCombo.blockSignals(False)

    def closeEvent(self, event):"""

content = content.replace(old_show, new_sync_method)

with open("novelwriter/gui/ai_assistant.py", "w") as f:
    f.write(content)

print("Sync patched.")
