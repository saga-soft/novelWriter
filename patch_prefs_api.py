import os
os.chdir("/home/ab/workspaces/novelWriter")
with open("novelwriter/dialogs/preferences.py", "r") as f:
    prefs = f.read()

# Replace the single API Key widget with three
old_api_key_ui = """        # API Key (only shown for non-local providers)
        self.aiApiKey = QLineEdit(self)
        self.aiApiKey.setEchoMode(QLineEdit.EchoMode.Password)
        self.aiApiKey.setPlaceholderText(self.tr("API Key (e.g., sk-...)"))
        self.aiApiKey.hide()
        if CONFIG.aiApiKey:
            self.aiApiKey.setText(CONFIG.aiApiKey)
        self.mainForm.addRow(
            self.tr("API Key"),
            self.aiApiKey,
            self.tr("Your API key for cloud providers."),
        )"""

new_api_key_ui = """        # API Keys (only shown for respective providers)
        self.aiApiKeyOpenAI = QLineEdit(self)
        self.aiApiKeyOpenAI.setEchoMode(QLineEdit.EchoMode.Password)
        self.aiApiKeyOpenAI.setPlaceholderText(self.tr("OpenAI API Key (sk-...)"))
        self.aiApiKeyOpenAI.hide()
        if getattr(CONFIG, 'aiApiKeyOpenAI', ''):
            self.aiApiKeyOpenAI.setText(CONFIG.aiApiKeyOpenAI)
        self.mainForm.addRow(self.tr("OpenAI API Key"), self.aiApiKeyOpenAI, self.tr("Your API key for OpenAI."))

        self.aiApiKeyAnthropic = QLineEdit(self)
        self.aiApiKeyAnthropic.setEchoMode(QLineEdit.EchoMode.Password)
        self.aiApiKeyAnthropic.setPlaceholderText(self.tr("Anthropic API Key (sk-ant-...)"))
        self.aiApiKeyAnthropic.hide()
        if getattr(CONFIG, 'aiApiKeyAnthropic', ''):
            self.aiApiKeyAnthropic.setText(CONFIG.aiApiKeyAnthropic)
        self.mainForm.addRow(self.tr("Anthropic API Key"), self.aiApiKeyAnthropic, self.tr("Your API key for Anthropic."))

        self.aiApiKeyGemini = QLineEdit(self)
        self.aiApiKeyGemini.setEchoMode(QLineEdit.EchoMode.Password)
        self.aiApiKeyGemini.setPlaceholderText(self.tr("Gemini API Key (AIza...)"))
        self.aiApiKeyGemini.hide()
        if getattr(CONFIG, 'aiApiKeyGemini', ''):
            self.aiApiKeyGemini.setText(CONFIG.aiApiKeyGemini)
        self.mainForm.addRow(self.tr("Gemini API Key"), self.aiApiKeyGemini, self.tr("Your API key for Google Gemini."))"""

prefs = prefs.replace(old_api_key_ui, new_api_key_ui)

# Update _toggle_api_fields
old_toggle = """        # API key is only relevant for cloud providers
        set_row_visible(self.aiApiKey, not is_local)
        self.aiApiKey.setEnabled(not is_local)
        if is_local:
            self.aiApiKey.clear()"""

new_toggle = """        # Show the correct API key field
        set_row_visible(self.aiApiKeyOpenAI, provider == "OpenAI")
        set_row_visible(self.aiApiKeyAnthropic, provider == "Anthropic")
        set_row_visible(self.aiApiKeyGemini, provider == "Google Gemini")"""

prefs = prefs.replace(old_toggle, new_toggle)

# Update _refreshAiModels to use the right key
old_refresh = """        provider = self.aiProvider.currentText()
        api_key = self.aiApiKey.text().strip()

        if provider == "Local / Llama.cpp":"""

new_refresh = """        provider = self.aiProvider.currentText()
        if provider == "OpenAI":
            api_key = self.aiApiKeyOpenAI.text().strip()
        elif provider == "Anthropic":
            api_key = self.aiApiKeyAnthropic.text().strip()
        elif provider == "Google Gemini":
            api_key = self.aiApiKeyGemini.text().strip()
        else:
            api_key = ""

        if provider == "Local / Llama.cpp":"""

prefs = prefs.replace(old_refresh, new_refresh)

# Update _doSave
old_save = """CONFIG.aiApiKey = self.aiApiKey.text()"""
new_save = """CONFIG.aiApiKeyOpenAI = self.aiApiKeyOpenAI.text()
        CONFIG.aiApiKeyAnthropic = self.aiApiKeyAnthropic.text()
        CONFIG.aiApiKeyGemini = self.aiApiKeyGemini.text()"""
prefs = prefs.replace(old_save, new_save)

with open("novelwriter/dialogs/preferences.py", "w") as f:
    f.write(prefs)
print("Preferences patched.")
