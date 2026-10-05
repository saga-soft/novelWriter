with open("novelwriter/gui/ai_assistant.py", "w") as f:
    f.write("""import json
import logging
from PyQt6.QtCore import Qt, QThread, pyqtSignal, pyqtSlot, QProcess
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextBrowser, 
    QTextEdit, QPushButton, QLabel, QMessageBox
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
        url = "http://127.0.0.1:8080/v1/chat/completions"
        headers = {"Content-Type": "application/json"}
        payload = {
            "messages": [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": self.user_prompt}
            ],
            "temperature": CONFIG.aiTemperature,
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
                            if data_str == "[DONE]":
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
        self.server_process = None
        self.worker = None

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
        
        self.startServerBtn = QPushButton("Start Server", self)
        self.startServerBtn.clicked.connect(self.toggleServer)
        
        self.headerLayout.addWidget(self.titleLabel)
        self.headerLayout.addStretch()
        self.headerLayout.addWidget(self.startServerBtn)
        self.layout.addLayout(self.headerLayout)
        
        # Chat History
        self.chatBrowser = QTextBrowser(self)
        self.chatBrowser.setOpenExternalLinks(True)
        self.layout.addWidget(self.chatBrowser, 1)

        # Input Area
        self.inputLayout = QHBoxLayout()
        self.inputEdit = QTextEdit(self)
        self.inputEdit.setFixedHeight(80)
        self.inputEdit.setPlaceholderText("Type your prompt here...")
        
        self.sendBtn = QPushButton("Send", self)
        self.sendBtn.setEnabled(False)
        self.sendBtn.clicked.connect(self.sendPrompt)

        self.inputLayout.addWidget(self.inputEdit, 1)
        self.inputLayout.addWidget(self.sendBtn)
        
        self.layout.addLayout(self.inputLayout)
        
    def toggleServer(self):
        if self.server_process is not None and self.server_process.state() != QProcess.ProcessState.NotRunning:
            self.stopServer()
        else:
            self.startServer()

    def startServer(self):
        if not CONFIG.aiEnginePath or not CONFIG.aiModelPath:
            QMessageBox.warning(self, "AI Assistant", "Please configure engine and model paths in Preferences.")
            return
            
        self.startServerBtn.setText("Starting...")
        self.startServerBtn.setEnabled(False)
        self.chatBrowser.append("<b>System:</b> Starting llama-server...")
        
        self.server_process = QProcess(self)
        self.server_process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        self.server_process.readyReadStandardOutput.connect(self.handleServerOutput)
        
        args = [
            "-m", CONFIG.aiModelPath,
            "-c", str(CONFIG.aiContextSize),
            "--port", "8080"
        ]
        
        self.server_process.start(CONFIG.aiEnginePath, args)
        
    def stopServer(self):
        if self.server_process is not None:
            self.server_process.terminate()
            self.server_process.waitForFinished(2000)
            self.server_process.kill()
            self.server_process = None
        self.startServerBtn.setText("Start Server")
        self.sendBtn.setEnabled(False)
        self.chatBrowser.append("<b>System:</b> Server stopped.")
        
    def handleServerOutput(self):
        if self.server_process is None:
            return
        output = self.server_process.readAllStandardOutput().data().decode('utf-8', errors='ignore')
        if "HTTP server listening" in output or "llama server listening" in output:
            self.startServerBtn.setText("Stop Server")
            self.startServerBtn.setEnabled(True)
            self.sendBtn.setEnabled(True)
            self.chatBrowser.append("<b>System:</b> Server ready.")
            
    def getActiveContext(self):
        text = self.mainGui.docEditor.getPlainText()
        max_chars = int((CONFIG.aiContextSize - 1000) * 3)
        if len(text) > max_chars:
            text = "... " + text[-max_chars:]
        return f"You are an AI assistant integrated into a writing app. Here is the current text the author is working on:\\n\\n---\\n{text}\\n---\\n\\nAssist the author as requested."

    def sendPrompt(self):
        prompt = self.inputEdit.toPlainText().strip()
        if not prompt:
            return
            
        self.inputEdit.clear()
        self.sendBtn.setEnabled(False)
        
        self.chatBrowser.append(f"<br><b>You:</b> {prompt}<br><b>AI:</b> ")
        
        system_prompt = self.getActiveContext()
        
        self.worker = AiWorker(system_prompt, prompt)
        self.worker.newToken.connect(self.onNewToken)
        self.worker.finishedGeneration.connect(self.onGenerationFinished)
        self.worker.errorGeneration.connect(self.onGenerationError)
        self.worker.start()
        
    def onNewToken(self, token: str):
        cursor = self.chatBrowser.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.chatBrowser.setTextCursor(cursor)
        self.chatBrowser.insertPlainText(token)
        
    def onGenerationFinished(self, response: str):
        self.sendBtn.setEnabled(True)
        self.chatBrowser.append("<br>")
        
    def onGenerationError(self, error: str):
        self.sendBtn.setEnabled(True)
        self.chatBrowser.append(f"<br><b>Error:</b> {error}<br>")
        
    def closeEvent(self, event):
        self.stopServer()
        if self.worker:
            self.worker.stop()
            self.worker.wait()
        super().closeEvent(event)
""")
