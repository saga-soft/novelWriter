import json
import time
import uuid
import datetime
from pathlib import Path
import logging
from PyQt6.QtCore import Qt, QThread, pyqtSignal, pyqtSlot, QObject
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextBrowser, 
    QTextEdit, QPushButton, QLabel, QMessageBox, QComboBox
)
import requests

from novelwriter import CONFIG, SHARED
from novelwriter.common import qtWeakLambda
from novelwriter.extensions.modified import NFlatIconButton

logger = logging.getLogger(__name__)


class ReturnFilter(QObject):
    def __init__(self, callback):
        super().__init__()
        self.callback = callback

    def eventFilter(self, obj, event):
        if event.type() == event.Type.KeyPress:
            if event.key() == Qt.Key.Key_Return and not (event.modifiers() & Qt.KeyboardModifier.ShiftModifier):
                self.callback()
                return True
        return super().eventFilter(obj, event)

class ChatManager:
    def __init__(self):
        self.chats_dir = CONFIG._confPath / "ai_chats"
        self.chats_dir.mkdir(exist_ok=True)
        
    def list_chats(self):
        chats = []
        for file in self.chats_dir.glob("*.json"):
            try:
                with open(file, "r") as f:
                    data = json.load(f)
                    chats.append(data)
            except:
                pass
        return sorted(chats, key=lambda x: x.get("updated_at", 0), reverse=True)
        
    def save_chat(self, chat_id, title, role, messages):
        file = self.chats_dir / f"{chat_id}.json"
        data = {
            "id": chat_id,
            "title": title,
            "role": role,
            "messages": messages,
            "updated_at": time.time()
        }
        with open(file, "w") as f:
            json.dump(data, f)
            
    def load_chat(self, chat_id):
        file = self.chats_dir / f"{chat_id}.json"
        if file.exists():
            try:
                with open(file, "r") as f:
                    return json.load(f)
            except:
                pass
        return None
        
    def delete_chat(self, chat_id):
        file = self.chats_dir / f"{chat_id}.json"
        if file.exists():
            file.unlink()

chat_mgr = ChatManager()

class AiWorker(QThread):
    newToken = pyqtSignal(str)
    finishedGeneration = pyqtSignal(str)
    errorGeneration = pyqtSignal(str)

    def __init__(self, messages: list, model: str, temperature: float):
        super().__init__()
        self.messages = messages
        self.model = model
        self.temperature = temperature
        self._is_running = True

    def stop(self):
        self._is_running = False

    def _get_request_config(self):
        """Get the request configuration based on the selected provider."""
        provider = CONFIG.aiProvider
        if provider == "OpenAI":
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
            }

        elif provider == "OpenAI":
            return {
                "url": "https://api.openai.com/v1/chat/completions",
                "headers": {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                "payload_format": "standard"
            }

        elif provider == "Anthropic":
            return {
                "url": "https://api.anthropic.com/v1/messages",
                "headers": {
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "Content-Type": "application/json"
                },
                "payload_format": "anthropic"
            }

        elif provider == "Google Gemini":
            return {
                "url": f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:streamGenerateContent?alt=sse&key={api_key}",
                "headers": {
                    "Content-Type": "application/json"
                },
                "payload_format": "gemini"
            }

        return {
            "url": f"{CONFIG.aiEndpoint}/v1/chat/completions",
            "headers": {"Content-Type": "application/json"},
            "payload_format": "standard"
        }

    def _build_payload(self, payload_format: str):
        """Build the payload based on the API format.

        The temperature parameter is only included for the Local
        (Llama.cpp) provider; cloud providers use their own defaults.
        """
        system_prompt = ""
        conversation = []
        for msg in self.messages:
            if msg.get("role") == "system":
                system_prompt = msg.get("content", "")
            else:
                conversation.append({"role": msg.get("role"), "content": msg.get("content", "")})
        if not conversation:
            conversation = [{"role": "user", "content": ""}]

        if payload_format == "standard":
            payload = {
                "model": self.model,
                "messages": conversation,
                "stream": True
            }
            if CONFIG.aiProvider == "Local / Llama.cpp":
                payload["temperature"] = self.temperature if self.temperature is not None else 0.7

        elif payload_format == "anthropic":
            payload = {
                "model": self.model,
                "system": system_prompt,
                "messages": conversation,
                "max_tokens": 4096,
                "stream": True
            }

        elif payload_format == "gemini":
            gemini_conversation = []
            for msg in conversation:
                # Gemini roles are 'user' and 'model'
                role = "user" if msg["role"] == "user" else "model"
                gemini_conversation.append({
                    "role": role,
                    "parts": [{"text": msg["content"]}]
                })
            
            payload = {
                "contents": gemini_conversation
            }
            if system_prompt:
                payload["systemInstruction"] = {
                    "parts": [{"text": system_prompt}]
                }

        return payload

    def run(self):
        config = self._get_request_config()
        url = config["url"]
        headers = config["headers"]
        payload_format = config["payload_format"]

        payload = self._build_payload(payload_format)
        # Thinking/reasoning parameters are only sent to the local engine
        if CONFIG.aiProvider == "Local / Llama.cpp":
            thinking_val = getattr(CONFIG, 'aiThinking', 'Off')
            if thinking_val and thinking_val.lower() != "off":
                payload["reasoning_effort"] = thinking_val
                payload["thinking"] = thinking_val

        full_response = ""
        try:
            with requests.post(url, headers=headers, json=payload, stream=True) as response:
                if response.status_code != 200:
                    self.errorGeneration.emit(f"Error: {response.status_code} - {response.text}")
                    return

                for line in response.iter_lines():
                    if not self._is_running:
                        break
                    if line:
                        decoded_line = line.decode('utf-8')
                        if decoded_line.startswith("data: "):
                            data_str = decoded_line[6:]
                            if data_str.strip() == "[DONE]":
                                break
                            try:
                                data = json.loads(data_str)
                                if payload_format == "standard":
                                    if "choices" in data and len(data["choices"]) > 0:
                                        delta = data["choices"][0].get("delta", {})
                                        content = delta.get("content", "")
                                        if content:
                                            full_response += content
                                            self.newToken.emit(content)
                                elif payload_format == "anthropic":
                                    if "delta" in data:
                                        content = data["delta"].get("content", "")
                                        if content:
                                            full_response += content
                                            self.newToken.emit(content)
                                elif payload_format == "gemini":
                                    if "candidates" in data and len(data["candidates"]) > 0:
                                        content = data["candidates"][0].get("content", {}).get("parts", [{}])[0].get("text", "")
                                        if content:
                                            full_response += content
                                            self.newToken.emit(content)
                            except json.JSONDecodeError:
                                pass
            self.finishedGeneration.emit(full_response)
        except Exception as e:
            self.errorGeneration.emit(str(e))

class AiAssistantDock(QWidget):
    def __init__(self, mainGui):
        super().__init__(parent=mainGui)
        self.mainGui = mainGui
        self.worker = None
        self.prompt_tokens = 0
        self.completion_tokens = 0
        self.is_thinking = False
        self.message_history = []
        self.first_token_time = 0
        self.current_response = ""
        self.current_chat_id = None
        self.current_chat_title = ""
        self.model = CONFIG.aiModel
        self.temperature = CONFIG.aiTemperature
        

        logger.debug("Create: AiAssistantDock")
        self.setObjectName("AiAssistantDock")

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(4, 4, 4, 4)

        # Header
        self.headerLayout = QHBoxLayout()
        self.titleLabel = QLabel("AI Assistant", self)
        font = self.titleLabel.font()
        font.setBold(True)
        self.titleLabel.setFont(font)

        self.headerLayout.addWidget(self.titleLabel)
        self.headerLayout.addStretch()
        self.layout.addLayout(self.headerLayout)
        
        # Recent Chats
        self.recentChatsLayout = QHBoxLayout()
        self.recentChatsCombo = QComboBox(self)
        self.recentChatsCombo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents)
        self.recentChatsCombo.activated.connect(self.loadSelectedChat)
        self.recentChatsLayout.addWidget(self.recentChatsCombo, 1)
        
        self.newChatBtn = QPushButton("New", self)
        self.newChatBtn.setToolTip("New Chat")
        self.newChatBtn.clicked.connect(self.newChat)
        self.recentChatsLayout.addWidget(self.newChatBtn)
        
        self.delChatBtn = QPushButton("Del", self)
        self.delChatBtn.setToolTip("Delete Chat")
        self.delChatBtn.clicked.connect(self.deleteChat)
        self.recentChatsLayout.addWidget(self.delChatBtn)
        
        self.layout.addLayout(self.recentChatsLayout)

        # Selectors Layout
        self.selectorsLayout = QHBoxLayout()
        
        self.selectorsLayout.addWidget(QLabel("Provider:", self))
        self.providerCombo = QComboBox(self)
        self.providerCombo.addItems(["Local / Llama.cpp", "OpenAI", "Anthropic", "Google Gemini"])
        self.providerCombo.setCurrentText(getattr(CONFIG, "aiProvider", "Local / Llama.cpp"))
        self.providerCombo.currentTextChanged.connect(self.changeProvider)
        self.selectorsLayout.addWidget(self.providerCombo)
        
        self.selectorsLayout.addSpacing(10)
        
        self.selectorsLayout.addWidget(QLabel("Role:", self))
        self.roleCombo = QComboBox(self)
        self.roleCombo.addItems(["Co-author", "Editor", "Publisher", "Reader"])
        self.roleCombo.setCurrentText(getattr(CONFIG, "aiActiveRole", "Co-author"))
        self.roleCombo.currentTextChanged.connect(self.changeRole)
        self.selectorsLayout.addWidget(self.roleCombo)
        
        self.selectorsLayout.addSpacing(10)
        
        self.selectorsLayout.addWidget(QLabel("Model:", self))
        self.modelCombo = QComboBox(self)
        self.modelCombo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents)
        self.modelCombo.setEditable(True)
        self.modelCombo.currentTextChanged.connect(self.changeModel)
        # Populate initial
        initial_model = getattr(CONFIG, 'aiModel', '')
        if initial_model:
            self.modelCombo.addItem(initial_model)
        self.selectorsLayout.addWidget(self.modelCombo)
        
        self.refreshModelBtn = QPushButton("↻", self)
        self.refreshModelBtn.setFixedSize(24, 24)
        self.refreshModelBtn.setToolTip("Refresh Models")
        self.refreshModelBtn.clicked.connect(self.refreshModels)
        self.selectorsLayout.addWidget(self.refreshModelBtn)
        
        self.selectorsLayout.addStretch()
        self.layout.addLayout(self.selectorsLayout)

        # Chat History
        self.chatBrowser = QTextBrowser(self)
        self.chatBrowser.setOpenExternalLinks(True)
        self.layout.addWidget(self.chatBrowser, 1)

        # Status & Cancel Area
        self.statusLayout = QHBoxLayout()
        self.statusLabel = QLabel("Ready.", self)
        font = self.statusLabel.font()
        font.setPointSize(max(8, font.pointSize() - 1))
        self.statusLabel.setFont(font)

        self.cancelBtn = QPushButton("Cancel", self)
        self.cancelBtn.setEnabled(False)
        self.cancelBtn.clicked.connect(self.cancelPrompt)

        self.statusLayout.addWidget(self.statusLabel, 1)
        self.statusLayout.addWidget(self.cancelBtn)
        self.layout.addLayout(self.statusLayout)

        # Input Area
        self.inputLayout = QHBoxLayout()
        self.inputEdit = QTextEdit(self)
        self.inputEdit.setFixedHeight(80)
        self.inputEdit.setPlaceholderText("Type your prompt here... (Enter to send, Shift+Enter for new line)")
        
        self.return_filter = ReturnFilter(self.sendPrompt)
        self.inputEdit.installEventFilter(self.return_filter)

        self.sendBtn = QPushButton("Send", self)
        self.sendBtn.clicked.connect(self.sendPrompt)

        self.inputLayout.addWidget(self.inputEdit, 1)
        self.inputLayout.addWidget(self.sendBtn)

        self.layout.addLayout(self.inputLayout)

        self.chatBrowser.append("<b>System:</b> Ready. The assistant will connect to your configured llama server endpoint.")
        self.refreshModels()
        self.refreshChatsList()

    def refreshChatsList(self):
        self.recentChatsCombo.blockSignals(True)
        self.recentChatsCombo.clear()
        chats = chat_mgr.list_chats()
        self.recentChatsCombo.addItem("-- Select Chat --", "")
        for chat in chats:
            self.recentChatsCombo.addItem(chat.get("title", "Untitled"), chat.get("id"))
            
        if self.current_chat_id:
            idx = self.recentChatsCombo.findData(self.current_chat_id)
            if idx >= 0:
                self.recentChatsCombo.setCurrentIndex(idx)
                
        self.recentChatsCombo.blockSignals(False)
        
    def loadSelectedChat(self, index):
        chat_id = self.recentChatsCombo.itemData(index)
        if not chat_id:
            return
            
        chat = chat_mgr.load_chat(chat_id)
        if chat:
            self.current_chat_id = chat_id
            self.current_chat_title = chat.get("title", "")
            self.message_history = chat.get("messages", [])
            
            # Set role if possible
            role = chat.get("role", "")
            if role:
                idx = self.roleCombo.findText(role)
                if idx >= 0:
                    self.roleCombo.setCurrentIndex(idx)
                    
            self.chatBrowser.clear()
            self.chatBrowser.append(f"<b>System:</b> Loaded chat: {self.current_chat_title}")
            for msg in self.message_history:
                if msg["role"] == "user":
                    self.chatBrowser.append(f"<br><b>You:</b> {msg['content']}")
                else:
                    self.chatBrowser.append(f"<br><b>{msg.get("agent", role)} says:</b> {msg["content"]}" )
            self.chatBrowser.append("<br>")
            self.statusLabel.setText("Chat loaded.")

    def newChat(self):
        self.current_chat_id = None
        self.current_chat_title = ""
        self.model = CONFIG.aiModel
        self.temperature = CONFIG.aiTemperature
        
        self.message_history = []
        self.chatBrowser.clear()
        self.chatBrowser.append("<b>System:</b> New chat started. Ready for prompt.")
        self.statusLabel.setText("Ready.")
        self.refreshChatsList()
        
    def deleteChat(self):
        chat_id = self.current_chat_id
        if not chat_id:
            chat_id = self.recentChatsCombo.itemData(self.recentChatsCombo.currentIndex())
            
        if chat_id:
            chat_mgr.delete_chat(chat_id)
            if chat_id == self.current_chat_id:
                self.newChat()
            else:
                self.refreshChatsList()

    def refreshModels(self):
        """Fetch the model list using the hardcoded base URLs for each provider.

        The endpoint field is only used for Local / Llama.cpp.
        """
        provider = getattr(CONFIG, 'aiProvider', 'Local / Llama.cpp')

        if provider == "Local / Llama.cpp":
            endpoint = getattr(CONFIG, 'aiEndpoint', '').strip().rstrip("/")
            if not endpoint:
                return
            url = f"{endpoint}/models" if endpoint.endswith("/v1") else f"{endpoint}/v1/models"
            headers = {}
        elif provider == "OpenAI":
            url = "https://api.openai.com/v1/models"
            headers = {"Authorization": f"Bearer {getattr(CONFIG, 'aiApiKeyOpenAI', '')}"}
        elif provider == "Anthropic":
            url = "https://api.anthropic.com/v1/models"
            headers = {
                "x-api-key": getattr(CONFIG, 'aiApiKeyAnthropic', ''),
                "anthropic-version": "2023-06-01"
            }
        elif provider == "Google Gemini":
            url = f"https://generativelanguage.googleapis.com/v1beta/models?key={getattr(CONFIG, 'aiApiKeyGemini', '')}"
            headers = {}
        else:
            return

        def fetch_models():
            try:
                r = requests.get(url, headers=headers, timeout=5)
                if r.status_code == 200:
                    data = r.json()
                    if provider == "Google Gemini":
                        # Gemini returns {"models": [{"name": "models/xxx", ...}]}
                        models = []
                        for m in data.get("models", []):
                            name = m.get("name", "")
                            if not name.startswith("models/"):
                                continue
                            # Only list models that can generate content
                            if "generateContent" not in m.get("supportedGenerationMethods", []):
                                continue
                            models.append({"id": name[len("models/"):]})
                        return models
                    return data.get("data", [])
            except Exception:
                pass
            return []
            
        import threading
        def worker():
            models = fetch_models()
            from PyQt6.QtCore import QMetaObject, Qt, Q_ARG
            QMetaObject.invokeMethod(self, "_updateModelsUI", Qt.ConnectionType.QueuedConnection, Q_ARG(list, models))
        
        threading.Thread(target=worker, daemon=True).start()

    @pyqtSlot(list)
    def _updateModelsUI(self, models: list):
        self.modelCombo.blockSignals(True)
        self.modelCombo.clear()
        current_model = getattr(CONFIG, 'aiModel', '')
        for m in models:
            self.modelCombo.addItem(m.get("id", ""))
        idx = self.modelCombo.findText(current_model)
        if idx >= 0:
            self.modelCombo.setCurrentIndex(idx)
        elif models:
            CONFIG.aiModel = models[0].get("id", "")
            self.modelCombo.setCurrentIndex(0)
            CONFIG.saveConfig()
        self.modelCombo.blockSignals(False)

    def changeProvider(self, provider_name: str):
        CONFIG.aiProvider = provider_name
        CONFIG.saveConfig()
        self.refreshModels()

    def changeRole(self, role_name: str):
        CONFIG.aiActiveRole = role_name
        CONFIG.saveConfig()
        
    def changeModel(self, model_name: str):
        if model_name:
            CONFIG.aiModel = model_name
            CONFIG.saveConfig()

    def getActiveContext(self):
        text = self.mainGui.docEditor.getText()
        context_size = getattr(CONFIG, 'aiContextSize', 8192)
        max_chars = int((context_size - 1000) * 3)
        if len(text) > max_chars:
            text = "... " + text[-max_chars:]

        role = self.roleCombo.currentText()
        if role == "Co-author":
            sys_prompt = getattr(CONFIG, 'aiPromptCoAuthor', '')
        elif role == "Editor":
            sys_prompt = getattr(CONFIG, 'aiPromptEditor', '')
        elif role == "Publisher":
            sys_prompt = getattr(CONFIG, 'aiPromptPublisher', '')
        else:
            sys_prompt = getattr(CONFIG, 'aiPromptReader', '')

        return f"{sys_prompt}\n\nHere is the current text the author is working on:\n\n---\n{text}\n---\n\nAssist the author as requested."

    def sendPrompt(self):
        prompt = self.inputEdit.toPlainText().strip()
        if not prompt:
            return
            
        role = self.roleCombo.currentText()
        
        if not self.current_chat_id:
            self.current_chat_id = str(uuid.uuid4())
            preview = prompt[:20] + "..." if len(prompt) > 20 else prompt
            date_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            self.current_chat_title = f"{role}: {preview} ({date_str})"

        self.inputEdit.clear()
        self.sendBtn.setEnabled(False)
        self.cancelBtn.setEnabled(True)

        self.chatBrowser.append(f"<br><b>You:</b> {prompt}<br><b>{role} says:</b> ")

        system_prompt = self.getActiveContext()
        
        self.message_history.append({"role": "user", "content": prompt})
        
        messages = [{"role": "system", "content": system_prompt}] + self.message_history
        
        history_text = " ".join([m["content"] for m in self.message_history])
        self.prompt_tokens = len(system_prompt + history_text) // 4
        self.completion_tokens = 0
        self.current_response = ""
        self.is_thinking = True
        self.first_token_time = 0
        self.statusLabel.setText(f"Thinking... (Prompt Tokens: ~{self.prompt_tokens})")

        provider = getattr(CONFIG, 'aiProvider', 'Local / Llama.cpp')
        
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
            
        self.worker = AiWorker(messages, self.model, self.temperature)
        self.worker.newToken.connect(self.onNewToken)
        self.worker.finishedGeneration.connect(self.onGenerationFinished)
        self.worker.errorGeneration.connect(self.onGenerationError)
        self.worker.start()

    def onNewToken(self, token: str):
        self.completion_tokens += 1
        self.current_response += token
        if self.is_thinking:
            self.is_thinking = False
            self.first_token_time = time.time()
            
        elapsed = time.time() - self.first_token_time if self.first_token_time else 0
        tps = self.completion_tokens / elapsed if elapsed > 0 else 0

        if self.completion_tokens % 3 == 0 or self.completion_tokens == 1:
            self.statusLabel.setText(f"Generating... (Prompt: ~{self.prompt_tokens} | Output: ~{self.completion_tokens} | Speed: {tps:.1f} t/s)")

        cursor = self.chatBrowser.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.chatBrowser.setTextCursor(cursor)
        self.chatBrowser.insertPlainText(token)

    def onGenerationFinished(self, response: str):
        self.sendBtn.setEnabled(True)
        self.cancelBtn.setEnabled(False)
        elapsed = time.time() - self.first_token_time if self.first_token_time else 0
        tps = self.completion_tokens / elapsed if elapsed > 0 else 0
        self.statusLabel.setText(f"Finished. (Prompt: ~{self.prompt_tokens} | Output: ~{self.completion_tokens} | Speed: {tps:.1f} t/s)")
        self.chatBrowser.append("<br>")
        self.message_history.append({"role": "assistant", "agent": self.roleCombo.currentText(), "content": self.current_response})
        
        chat_mgr.save_chat(self.current_chat_id, self.current_chat_title, self.roleCombo.currentText(), self.message_history)
        self.refreshChatsList()

    def onGenerationError(self, error: str):
        self.sendBtn.setEnabled(True)
        self.cancelBtn.setEnabled(False)
        self.statusLabel.setText("Error occurred.")
        self.chatBrowser.append(f"<br><b>Error:</b> {error}<br>")
        
    def cancelPrompt(self):
        if self.worker:
            self.worker.stop()
        self.sendBtn.setEnabled(True)
        self.cancelBtn.setEnabled(False)
        self.statusLabel.setText(f"Cancelled. (Prompt: ~{self.prompt_tokens} | Output: ~{self.completion_tokens})")
        self.chatBrowser.append("<br><i>[Generation Cancelled]</i><br>")
        if self.current_response:
            self.message_history.append({"role": "assistant", "agent": self.roleCombo.currentText(), "content": self.current_response})
            chat_mgr.save_chat(self.current_chat_id, self.current_chat_title, self.roleCombo.currentText(), self.message_history)
            self.refreshChatsList()

    def closeEvent(self, event):
        if self.worker:
            self.worker.stop()
            self.worker.wait()
        super().closeEvent(event)
