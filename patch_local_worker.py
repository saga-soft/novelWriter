import os

with open("novelwriter/gui/ai_assistant.py", "r") as f:
    ai_dock = f.read()

old_get_config = """        if provider == "OpenAI":
            api_key = getattr(CONFIG, 'aiApiKeyOpenAI', '')
        elif provider == "Anthropic":
            api_key = getattr(CONFIG, 'aiApiKeyAnthropic', '')
        elif provider == "Google Gemini":
            api_key = getattr(CONFIG, 'aiApiKeyGemini', '')
        else:
            api_key = ''

        if provider == "Local / Llama.cpp":
            return {
                "url": f"{CONFIG.aiEndpoint}/v1/chat/completions",
                "headers": {"Content-Type": "application/json"},
                "payload_format": "standard"
            }"""

new_get_config = """        if provider == "OpenAI":
            api_key = getattr(CONFIG, 'aiApiKeyOpenAI', '')
        elif provider == "Anthropic":
            api_key = getattr(CONFIG, 'aiApiKeyAnthropic', '')
        elif provider == "Google Gemini":
            api_key = getattr(CONFIG, 'aiApiKeyGemini', '')
        elif provider == "Local / Llama.cpp":
            api_key = getattr(CONFIG, 'aiApiKeyLocal', '')
        else:
            api_key = ''

        if provider == "Local / Llama.cpp":
            headers = {"Content-Type": "application/json"}
            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"
            return {
                "url": f"{CONFIG.aiEndpoint}/v1/chat/completions",
                "headers": headers,
                "payload_format": "standard"
            }"""

ai_dock = ai_dock.replace(old_get_config, new_get_config)

# Fix OpenAI empty payload checking logic 
old_send_prompt = """        provider = getattr(CONFIG, 'aiProvider', 'Local / Llama.cpp')
        if provider == "OpenAI" and not getattr(CONFIG, 'aiApiKeyOpenAI', ''):
            QMessageBox.warning(self, "AI Assistant", "Please configure the OpenAI API Key in Preferences.")
            self.sendBtn.setEnabled(True)
            self.cancelBtn.setEnabled(False)
            self.clearBtn.setEnabled(True)
            return"""

new_send_prompt = """        provider = getattr(CONFIG, 'aiProvider', 'Local / Llama.cpp')
        
        # Local endpoint guard
        if provider == "Local / Llama.cpp":
            if not getattr(CONFIG, 'aiEndpoint', None):
                QMessageBox.warning(self, "AI Assistant", "Please configure the AI Endpoint in Preferences.")
                return
                
        if provider == "OpenAI" and not getattr(CONFIG, 'aiApiKeyOpenAI', ''):
            QMessageBox.warning(self, "AI Assistant", "Please configure the OpenAI API Key in Preferences.")
            self.sendBtn.setEnabled(True)
            self.cancelBtn.setEnabled(False)
            self.clearBtn.setEnabled(True)
            return"""

ai_dock = ai_dock.replace(old_send_prompt, new_send_prompt)

# Remove the old endpoint guard
ai_dock = ai_dock.replace("""        if getattr(CONFIG, 'aiProvider', 'Local / Llama.cpp') == "Local / Llama.cpp":
            if not getattr(CONFIG, 'aiEndpoint', None):
                QMessageBox.warning(self, "AI Assistant", "Please configure the AI Endpoint in Preferences.")
                return\n\n""", "")

# Also add the Provider dropdown
old_selectors = """        # Selectors Layout
        self.selectorsLayout = QHBoxLayout()
        
        self.selectorsLayout.addWidget(QLabel("Role:", self))"""

new_selectors = """        # Selectors Layout
        self.selectorsLayout = QHBoxLayout()
        
        self.selectorsLayout.addWidget(QLabel("Provider:", self))
        self.providerCombo = QComboBox(self)
        self.providerCombo.addItems(["Local / Llama.cpp", "OpenAI", "Anthropic", "Google Gemini"])
        self.providerCombo.setCurrentText(getattr(CONFIG, "aiProvider", "Local / Llama.cpp"))
        self.providerCombo.currentTextChanged.connect(self.changeProvider)
        self.selectorsLayout.addWidget(self.providerCombo)
        
        self.selectorsLayout.addSpacing(10)
        
        self.selectorsLayout.addWidget(QLabel("Role:", self))"""

ai_dock = ai_dock.replace(old_selectors, new_selectors)

old_change = """    def changeRole(self, role_name: str):
        CONFIG.aiActiveRole = role_name
        CONFIG.saveConfig()"""

new_change = """    def changeProvider(self, provider_name: str):
        CONFIG.aiProvider = provider_name
        CONFIG.saveConfig()
        self.refreshModels()

    def changeRole(self, role_name: str):
        CONFIG.aiActiveRole = role_name
        CONFIG.saveConfig()"""

ai_dock = ai_dock.replace(old_change, new_change)

with open("novelwriter/gui/ai_assistant.py", "w") as f:
    f.write(ai_dock)

print("Worker patched.")
