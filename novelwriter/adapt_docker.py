import os
import re

os.chdir("/home/ab/workspaces/novelWriter")

# 1. Update config.py
with open("novelwriter/config.py", "r") as f:
    config = f.read()

config = config.replace('aiEnginePath', 'aiEndpoint')
config = config.replace('self.aiEndpoint = ""', 'self.aiEndpoint = "http://127.0.0.1:8080"')
config = config.replace('parser.getStr(sec, "enginePath"', 'parser.getStr(sec, "endpoint"')
config = config.replace('"enginePath": self.aiEndpoint', '"endpoint": self.aiEndpoint')

# Clean up aiModelPath
config = config.replace('        "aiModelPath",\n', '')
config = config.replace('        self.aiModelPath = ""\n', '')
config = config.replace('        self.aiModelPath = parser.getStr(sec, "modelPath", self.aiModelPath)\n', '')
config = config.replace('            "modelPath": self.aiModelPath,\n', '')

with open("novelwriter/config.py", "w") as f:
    f.write(config)


# 2. Update preferences.py
with open("novelwriter/dialogs/preferences.py", "r") as f:
    prefs = f.read()

prefs = prefs.replace('self.aiEnginePath = QLineEdit(self)', 'self.aiEndpoint = QLineEdit(self)')
prefs = prefs.replace('self.aiEnginePath.setText(CONFIG.aiEnginePath)', 'self.aiEndpoint.setText(CONFIG.aiEndpoint)')
prefs = prefs.replace('self.aiEnginePath,', 'self.aiEndpoint,')
prefs = prefs.replace('llama-server Path', 'AI Server Endpoint')
prefs = prefs.replace('Absolute path to the llama.cpp server executable.', 'Endpoint URL (e.g. http://127.0.0.1:8080)')
prefs = prefs.replace('CONFIG.aiEnginePath = self.aiEnginePath.text()', 'CONFIG.aiEndpoint = self.aiEndpoint.text()')

model_path_str = """        # Model Path
        self.aiModelPath = QLineEdit(self)
        self.aiModelPath.setText(CONFIG.aiModelPath)
        self.mainForm.addRow(
            self.tr("Model File (.gguf)"),
            self.aiModelPath,
            self.tr("Absolute path to the model file."),
        )"""
prefs = prefs.replace(model_path_str, "")
prefs = prefs.replace('        CONFIG.aiModelPath = self.aiModelPath.text()\n', '')

with open("novelwriter/dialogs/preferences.py", "w") as f:
    f.write(prefs)


# 3. Update guimain.py
with open("novelwriter/guimain.py", "r") as f:
    guimain = f.read()

guimain = guimain.replace('            if is_visible:\n                self.aiAssistantPane.startServer()', '')

with open("novelwriter/guimain.py", "w") as f:
    f.write(guimain)

print("Patching completed")
