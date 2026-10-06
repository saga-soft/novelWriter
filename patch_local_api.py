import os
os.chdir("/home/ab/workspaces/novelWriter")

# 1. Update config.py
with open("novelwriter/config.py", "r") as f:
    config = f.read()

config = config.replace('"aiApiKeyOpenAI",', '"aiApiKeyLocal",\n        "aiApiKeyOpenAI",')
config = config.replace('self.aiApiKeyOpenAI = ""', 'self.aiApiKeyLocal = "sk-dummy"\n        self.aiApiKeyOpenAI = ""')
config = config.replace('self.aiApiKeyOpenAI = parser.getStr(sec, "apiKeyOpenAI", self.aiApiKeyOpenAI)', 'self.aiApiKeyLocal = parser.getStr(sec, "apiKeyLocal", self.aiApiKeyLocal)\n        self.aiApiKeyOpenAI = parser.getStr(sec, "apiKeyOpenAI", self.aiApiKeyOpenAI)')
config = config.replace('"apiKeyOpenAI": self.aiApiKeyOpenAI,', '"apiKeyLocal": self.aiApiKeyLocal,\n            "apiKeyOpenAI": self.aiApiKeyOpenAI,')

with open("novelwriter/config.py", "w") as f:
    f.write(config)

# 2. Update preferences.py
with open("novelwriter/dialogs/preferences.py", "r") as f:
    prefs = f.read()

local_key_ui = """        self.aiApiKeyLocal = QLineEdit(self)
        self.aiApiKeyLocal.setEchoMode(QLineEdit.EchoMode.Password)
        self.aiApiKeyLocal.setPlaceholderText(self.tr("Local API Key (sk-...)"))
        self.aiApiKeyLocal.hide()
        if getattr(CONFIG, 'aiApiKeyLocal', ''):
            self.aiApiKeyLocal.setText(CONFIG.aiApiKeyLocal)
        self.mainForm.addRow(self.tr("Local API Key"), self.aiApiKeyLocal, self.tr("Your API key for local providers."))
        
        self.aiApiKeyOpenAI = QLineEdit(self)"""

prefs = prefs.replace("self.aiApiKeyOpenAI = QLineEdit(self)", local_key_ui)

prefs = prefs.replace(
    'set_row_visible(self.aiApiKeyOpenAI, provider == "OpenAI")',
    'set_row_visible(self.aiApiKeyLocal, is_local)\n        set_row_visible(self.aiApiKeyOpenAI, provider == "OpenAI")'
)

prefs = prefs.replace(
    'CONFIG.aiApiKeyOpenAI = self.aiApiKeyOpenAI.text()',
    'CONFIG.aiApiKeyLocal = self.aiApiKeyLocal.text()\n        CONFIG.aiApiKeyOpenAI = self.aiApiKeyOpenAI.text()'
)

with open("novelwriter/dialogs/preferences.py", "w") as f:
    f.write(prefs)

print("Local API key patched.")
