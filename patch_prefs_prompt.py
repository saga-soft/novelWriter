import os
os.chdir("/home/ab/workspaces/novelWriter")
with open("novelwriter/dialogs/preferences.py", "r") as f:
    content = f.read()

# Add text edit for system prompt
prompt_widget = """
        # System Prompt
        self.aiSystemPrompt = QTextEdit(self)
        self.aiSystemPrompt.setFixedHeight(80)
        self.aiSystemPrompt.setPlainText(CONFIG.aiSystemPrompt)
        self.mainForm.addRow(
            self.tr("System Specialization"),
            self.aiSystemPrompt,
            self.tr("Pre-prompt to define the assistant's behavior/role."),
        )

"""
# We insert it after aiTemperature
content = content.replace('        self.aiTemperature.setValue(CONFIG.aiTemperature)\n        self.mainForm.addRow(\n            self.tr("Temperature"),\n            self.aiTemperature,\n            self.tr("Higher values make output more random."),\n        )', '        self.aiTemperature.setValue(CONFIG.aiTemperature)\n        self.mainForm.addRow(\n            self.tr("Temperature"),\n            self.aiTemperature,\n            self.tr("Higher values make output more random."),\n        )\n' + prompt_widget)

content = content.replace('CONFIG.aiTemperature = self.aiTemperature.value()', 'CONFIG.aiTemperature = self.aiTemperature.value()\n        CONFIG.aiSystemPrompt = self.aiSystemPrompt.toPlainText().strip()')

with open("novelwriter/dialogs/preferences.py", "w") as f:
    f.write(content)
