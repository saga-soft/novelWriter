import os
os.chdir("/home/ab/workspaces/novelWriter")

# 1. config.py
with open("novelwriter/config.py", "r") as f:
    config = f.read()

config = config.replace('"aiTemperature",', '"aiTemperature",\n        "aiThinking",')
config = config.replace('self.aiTemperature = 0.7', 'self.aiTemperature = 0.7\n        self.aiThinking = "Off"')
config = config.replace('self.aiTemperature = parser.getFloat(sec, "temperature", self.aiTemperature)', 'self.aiTemperature = parser.getFloat(sec, "temperature", self.aiTemperature)\n        self.aiThinking = parser.getStr(sec, "thinking", self.aiThinking)')
config = config.replace('"temperature": self.aiTemperature,', '"temperature": self.aiTemperature,\n            "thinking": self.aiThinking,')

with open("novelwriter/config.py", "w") as f:
    f.write(config)

# 2. preferences.py
with open("novelwriter/dialogs/preferences.py", "r") as f:
    prefs = f.read()

thinking_ui = """        # Thinking
        self.aiThinkingCombo = NComboBox(self)
        self.aiThinkingCombo.addItems(["Off", "low", "med", "high", "xhigh"])
        self.aiThinkingCombo.setCurrentText(getattr(CONFIG, 'aiThinking', 'Off'))
        self.mainForm.addRow(
            self.tr("Thinking Variable"),
            self.aiThinkingCombo,
            self.tr("Thinking/reasoning effort for supported models."),
        )
"""
prefs = prefs.replace('        # Co-author', thinking_ui + '\n        # Co-author')
prefs = prefs.replace('CONFIG.aiTemperature = self.aiTemperature.value()', 'CONFIG.aiTemperature = self.aiTemperature.value()\n        CONFIG.aiThinking = self.aiThinkingCombo.currentText()')

with open("novelwriter/dialogs/preferences.py", "w") as f:
    f.write(prefs)

# 3. ai_assistant.py
with open("novelwriter/gui/ai_assistant.py", "r") as f:
    ai_dock = f.read()

payload_old = """        payload = {
            "model": getattr(CONFIG, 'aiModel', ''),
            "messages": self.messages,
            "temperature": getattr(CONFIG, 'aiTemperature', 0.7),
            "stream": True
        }"""
payload_new = """        payload = {
            "model": getattr(CONFIG, 'aiModel', ''),
            "messages": self.messages,
            "temperature": getattr(CONFIG, 'aiTemperature', 0.7),
            "stream": True
        }
        
        thinking_val = getattr(CONFIG, 'aiThinking', 'Off')
        if thinking_val and thinking_val.lower() != "off":
            payload["reasoning_effort"] = thinking_val
            payload["thinking"] = thinking_val"""

ai_dock = ai_dock.replace(payload_old, payload_new)

with open("novelwriter/gui/ai_assistant.py", "w") as f:
    f.write(ai_dock)

print("Thinking variable applied successfully.")
