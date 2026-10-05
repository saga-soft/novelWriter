import json
import logging
from PyQt6.QtCore import Qt, QThread, pyqtSignal, pyqtSlot
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextBrowser, 
    QTextEdit, QPushButton, QLabel, QMessageBox, QComboBox
)
import requests

from novelwriter import CONFIG, SHARED
from novelwriter.common import qtWeakLambda
from novelwriter.extensions.modified import NFlatIconButton

logger = logging.getLogger(__name__)

class AiWorker(QThread):
    newToken = pyqtSignal(str)
    finishedGeneration = pyqtSignal(str)
    errorGeneration = pyqtSignal(str)

    def __init__(self, system_prompt: str, user_prompt: str):
        super().__init__()
        self.system_prompt = system_prompt
        self.user_prompt = user_prompt
        self._is_running = True

    def stop(self):
        self._is_running = False

    def run(self):
        base_url = CONFIG.aiEndpoint.rstrip('/') if hasattr(CONFIG, 'aiEndpoint') and CONFIG.aiEndpoint else "http://127.0.0.1:8080"
        url = f"{base_url}/chat/completions" if base_url.endswith("/v1") else f"{base_url}/v1/chat/completions"
        headers = {"Content-Type": "application/json"}
        payload = {
            "model": getattr(CONFIG, 'aiModel', ''),
            "messages": [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": self.user_prompt}
            ],
            "temperature": getattr(CONFIG, 'aiTemperature', 0.7),
            "stream": True
        }
        
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
                                if "choices" in data and len(data["choices"]) > 0:
                                    delta = data["choices"][0].get("delta", {})
                                    content = delta.get("content", "")
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

        # Selectors Layout
        self.selectorsLayout = QHBoxLayout()
        
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
        self.inputEdit.setPlaceholderText("Type your prompt here...")

        self.sendBtn = QPushButton("Send", self)
        self.sendBtn.clicked.connect(self.sendPrompt)

        self.inputLayout.addWidget(self.inputEdit, 1)
        self.inputLayout.addWidget(self.sendBtn)

        self.layout.addLayout(self.inputLayout)

        self.chatBrowser.append("<b>System:</b> Ready. The assistant will connect to your configured llama server endpoint.")
        self.refreshModels()

    def refreshModels(self):
        endpoint = getattr(CONFIG, 'aiEndpoint', '').strip().rstrip("/")
        if not endpoint:
            return
        
        url = f"{endpoint}/models" if endpoint.endswith("/v1") else f"{endpoint}/v1/models"
        
        def fetch_models():
            try:
                r = requests.get(url, timeout=3)
                if r.status_code == 200:
                    return r.json().get("data", [])
            except:
                pass
            return []
            
        # We'll just do it synchronously for simplicity in the UI thread since it's a quick local request,
        # but normally we'd use a thread.
        import threading
        def worker():
            models = fetch_models()
            def update_ui():
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
                self.modelCombo.blockSignals(False)
            # Use QMetaObject to invoke on main thread
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
        if not getattr(CONFIG, 'aiEndpoint', None):
            QMessageBox.warning(self, "AI Assistant", "Please configure the AI Endpoint in Preferences.")
            return

        prompt = self.inputEdit.toPlainText().strip()
        if not prompt:
            return

        self.inputEdit.clear()
        self.sendBtn.setEnabled(False)
        self.cancelBtn.setEnabled(True)

        self.chatBrowser.append(f"<br><b>You:</b> {prompt}<br><b>AI:</b> ")

        system_prompt = self.getActiveContext()
        
        self.prompt_tokens = len(system_prompt + prompt) // 4
        self.completion_tokens = 0
        self.is_thinking = True
        self.statusLabel.setText(f"Thinking... (Prompt Tokens: ~{self.prompt_tokens})")

        self.worker = AiWorker(system_prompt, prompt)
        self.worker.newToken.connect(self.onNewToken)
        self.worker.finishedGeneration.connect(self.onGenerationFinished)
        self.worker.errorGeneration.connect(self.onGenerationError)
        self.worker.start()

    def onNewToken(self, token: str):
        self.completion_tokens += 1
        if self.is_thinking:
            self.is_thinking = False

        if self.completion_tokens % 3 == 0 or self.completion_tokens == 1:
            self.statusLabel.setText(f"Generating... (Prompt: ~{self.prompt_tokens} | Output: ~{self.completion_tokens})")

        cursor = self.chatBrowser.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.chatBrowser.setTextCursor(cursor)
        self.chatBrowser.insertPlainText(token)

    def onGenerationFinished(self, response: str):
        self.sendBtn.setEnabled(True)
        self.cancelBtn.setEnabled(False)
        self.statusLabel.setText(f"Finished. (Prompt: ~{self.prompt_tokens} | Output: ~{self.completion_tokens})")
        self.chatBrowser.append("<br>")

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

    def closeEvent(self, event):
        if self.worker:
            self.worker.stop()
            self.worker.wait()
        super().closeEvent(event)
