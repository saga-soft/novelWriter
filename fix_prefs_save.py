with open("novelwriter/dialogs/preferences.py", "r") as f:
    content = f.read()

save_section = """
        CONFIG.aiEnabled = self.aiEnabled.isChecked()
        CONFIG.aiEndpoint = self.aiEndpoint.text()
        CONFIG.aiContextSize = self.aiContextSize.value()
        CONFIG.aiTemperature = self.aiTemperature.value()
"""
content = content.replace('CONFIG.vimMode = vimMode', 'CONFIG.vimMode = vimMode' + save_section)

with open("novelwriter/dialogs/preferences.py", "w") as f:
    f.write(content)
