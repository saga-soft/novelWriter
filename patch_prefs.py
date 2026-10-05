import os

os.chdir("/home/ab/workspaces/novelWriter")
with open("novelwriter/dialogs/preferences.py", "r") as f:
    content = f.read()

# Add AI Settings section
ai_section = """
        # AI Assistant
        # ============

        title = self.tr("AI Assistant")
        section += 1
        self.sidebar.addButton(title, section)
        self.mainForm.addGroupLabel(title, section)

        # Enable AI
        self.aiEnabled = NSwitch(self)
        self.aiEnabled.setChecked(CONFIG.aiEnabled)
        self.mainForm.addRow(
            self.tr("Enable AI Assistant"),
            self.aiEnabled,
            self.tr("Turn on the AI sidebar."),
        )
        
        # Engine Path
        self.aiEnginePath = QLineEdit(self)
        self.aiEnginePath.setText(CONFIG.aiEnginePath)
        self.mainForm.addRow(
            self.tr("llama-server Path"),
            self.aiEnginePath,
            self.tr("Absolute path to the llama.cpp server executable."),
        )

        # Model Path
        self.aiModelPath = QLineEdit(self)
        self.aiModelPath.setText(CONFIG.aiModelPath)
        self.mainForm.addRow(
            self.tr("Model File (.gguf)"),
            self.aiModelPath,
            self.tr("Absolute path to the model file."),
        )
        
        # Context Size
        self.aiContextSize = NSpinBox(self)
        self.aiContextSize.setRange(512, 128000)
        self.aiContextSize.setSingleStep(1024)
        self.aiContextSize.setValue(CONFIG.aiContextSize)
        self.mainForm.addRow(
            self.tr("Context Size"),
            self.aiContextSize,
            self.tr("Context window size (-c parameter)."),
        )
        
        # Temperature
        self.aiTemperature = NDoubleSpinBox(self)
        self.aiTemperature.setRange(0.0, 2.0)
        self.aiTemperature.setSingleStep(0.1)
        self.aiTemperature.setValue(CONFIG.aiTemperature)
        self.mainForm.addRow(
            self.tr("Temperature"),
            self.aiTemperature,
            self.tr("Higher values make output more random."),
        )

        """

content = content.replace('self.mainForm.finalise()', ai_section + 'self.mainForm.finalise()')

# Also save the values in _doSave
save_section = """
        CONFIG.aiEnabled = self.aiEnabled.isChecked()
        CONFIG.aiEnginePath = self.aiEnginePath.text()
        CONFIG.aiModelPath = self.aiModelPath.text()
        CONFIG.aiContextSize = self.aiContextSize.value()
        CONFIG.aiTemperature = self.aiTemperature.value()

        """
content = content.replace('CONFIG.vimMode = self.vimMode.isChecked()', 'CONFIG.vimMode = self.vimMode.isChecked()' + save_section)

with open("novelwriter/dialogs/preferences.py", "w") as f:
    f.write(content)

print("Success")
