import os
os.chdir("/home/ab/workspaces/novelWriter")
with open("novelwriter/gui/ai_assistant.py", "r") as f:
    ai_dock = f.read()

# Remove api_key from AiWorker init and fetch from CONFIG in _get_request_config
old_worker_init = """    def __init__(self, messages: list, model: str, temperature: float, api_key: str):
        super().__init__()
        self.messages = messages
        self.model = model
        self.temperature = temperature
        self.api_key = api_key
        self._is_running = True"""

new_worker_init = """    def __init__(self, messages: list, model: str, temperature: float):
        super().__init__()
        self.messages = messages
        self.model = model
        self.temperature = temperature
        self._is_running = True"""

old_get_config = """    def _get_request_config(self):
        \"\"\"Get the request configuration based on the selected provider.\"\"\"
        provider = CONFIG.aiProvider
        api_key = self.api_key"""

new_get_config = """    def _get_request_config(self):
        \"\"\"Get the request configuration based on the selected provider.\"\"\"
        provider = CONFIG.aiProvider
        if provider == "OpenAI":
            api_key = getattr(CONFIG, 'aiApiKeyOpenAI', '')
        elif provider == "Anthropic":
            api_key = getattr(CONFIG, 'aiApiKeyAnthropic', '')
        elif provider == "Google Gemini":
            api_key = getattr(CONFIG, 'aiApiKeyGemini', '')
        else:
            api_key = ''"""

# We also need to fix self.api_key usage in Gemini payload builder:
old_payload_gemini = """                "key": self.api_key"""
new_payload_gemini = """                "key": getattr(CONFIG, 'aiApiKeyGemini', '')"""

ai_dock = ai_dock.replace(old_worker_init, new_worker_init)
ai_dock = ai_dock.replace(old_get_config, new_get_config)
ai_dock = ai_dock.replace(old_payload_gemini, new_payload_gemini)

# Now in AiAssistantDock __init__, remove self.api_key
ai_dock = ai_dock.replace('self.api_key = getattr(CONFIG, \'aiApiKey\', \'\')', '')
ai_dock = ai_dock.replace('self.api_key = CONFIG.aiApiKey', '')

# In sendPrompt, don't pass api_key to AiWorker
old_worker_call = """        self.worker = AiWorker(messages, self.model, self.temperature, self.api_key)"""
new_worker_call = """        provider = getattr(CONFIG, 'aiProvider', 'Local / Llama.cpp')
        if provider == "OpenAI" and not getattr(CONFIG, 'aiApiKeyOpenAI', ''):
            QMessageBox.warning(self, "AI Assistant", "Please configure the OpenAI API Key in Preferences.")
            self.sendBtn.setEnabled(True)
            self.cancelBtn.setEnabled(False)
            self.clearBtn.setEnabled(True)
            return
        elif provider == "Anthropic" and not getattr(CONFIG, 'aiApiKeyAnthropic', ''):
            QMessageBox.warning(self, "AI Assistant", "Please configure the Anthropic API Key in Preferences.")
            self.sendBtn.setEnabled(True)
            self.cancelBtn.setEnabled(False)
            self.clearBtn.setEnabled(True)
            return
        elif provider == "Google Gemini" and not getattr(CONFIG, 'aiApiKeyGemini', ''):
            QMessageBox.warning(self, "AI Assistant", "Please configure the Gemini API Key in Preferences.")
            self.sendBtn.setEnabled(True)
            self.cancelBtn.setEnabled(False)
            self.clearBtn.setEnabled(True)
            return
            
        self.worker = AiWorker(messages, self.model, self.temperature)"""

ai_dock = ai_dock.replace(old_worker_call, new_worker_call)

# Update refreshModels to use the correct API key
old_refresh = """        elif provider == "OpenAI":
            url = "https://api.openai.com/v1/models"
            headers = {"Authorization": f"Bearer {getattr(CONFIG, 'aiApiKey', '')}"}
        elif provider == "Anthropic":
            url = "https://api.anthropic.com/v1/models"
            headers = {
                "x-api-key": getattr(CONFIG, 'aiApiKey', ''),
                "anthropic-version": "2023-06-01"
            }
        elif provider == "Google Gemini":
            url = f"https://generativelanguage.googleapis.com/v1beta/models?key={getattr(CONFIG, 'aiApiKey', '')}\""""

new_refresh = """        elif provider == "OpenAI":
            url = "https://api.openai.com/v1/models"
            headers = {"Authorization": f"Bearer {getattr(CONFIG, 'aiApiKeyOpenAI', '')}"}
        elif provider == "Anthropic":
            url = "https://api.anthropic.com/v1/models"
            headers = {
                "x-api-key": getattr(CONFIG, 'aiApiKeyAnthropic', ''),
                "anthropic-version": "2023-06-01"
            }
        elif provider == "Google Gemini":
            url = f"https://generativelanguage.googleapis.com/v1beta/models?key={getattr(CONFIG, 'aiApiKeyGemini', '')}\""""

ai_dock = ai_dock.replace(old_refresh, new_refresh)

# Add event filter to inputEdit for Shift+Enter vs Enter
event_filter_code = """class ReturnFilter(QObject):
    def __init__(self, callback):
        super().__init__()
        self.callback = callback

    def eventFilter(self, obj, event):
        if event.type() == event.Type.KeyPress:
            if event.key() == Qt.Key.Key_Return and not (event.modifiers() & Qt.KeyboardModifier.ShiftModifier):
                self.callback()
                return True
        return super().eventFilter(obj, event)

class ChatManager:"""

ai_dock = ai_dock.replace('class ChatManager:', event_filter_code)
ai_dock = ai_dock.replace('from PyQt6.QtCore import Qt, QThread, pyqtSignal, pyqtSlot', 'from PyQt6.QtCore import Qt, QThread, pyqtSignal, pyqtSlot, QObject')

# Install event filter in AiAssistantDock __init__
old_input = """        self.inputEdit.setPlaceholderText("Type your prompt here...")

        self.sendBtn = QPushButton("Send", self)"""

new_input = """        self.inputEdit.setPlaceholderText("Type your prompt here... (Enter to send, Shift+Enter for new line)")
        
        self.return_filter = ReturnFilter(self.sendPrompt)
        self.inputEdit.installEventFilter(self.return_filter)

        self.sendBtn = QPushButton("Send", self)"""

ai_dock = ai_dock.replace(old_input, new_input)

# Add max_tokens to Anthropic payload and fix streaming
old_anthropic = """        elif payload_format == "anthropic":
            payload = {
                "model": self.model,
                "system": system_prompt,
                "messages": conversation,
                "stream": True
            }"""

new_anthropic = """        elif payload_format == "anthropic":
            payload = {
                "model": self.model,
                "system": system_prompt,
                "messages": conversation,
                "max_tokens": 4096,
                "stream": True
            }"""

ai_dock = ai_dock.replace(old_anthropic, new_anthropic)

# Fix Gemini streaming URL
old_gemini_url = """                "url": f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:streamGenerateContent?key={api_key}","""
new_gemini_url = """                "url": f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:streamGenerateContent?alt=sse&key={api_key}","""
ai_dock = ai_dock.replace(old_gemini_url, new_gemini_url)

with open("novelwriter/gui/ai_assistant.py", "w") as f:
    f.write(ai_dock)

print("AI assistant patched.")
