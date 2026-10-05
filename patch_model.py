import os
os.chdir("/home/ab/workspaces/novelWriter")
with open("novelwriter/config.py", "r") as f:
    config = f.read()

config = config.replace('"aiEndpoint",', '"aiEndpoint",\n        "aiModel",')
config = config.replace('self.aiEndpoint = "http://127.0.0.1:8080"', 'self.aiEndpoint = "http://127.0.0.1:8080"\n        self.aiModel = ""')
config = config.replace('self.aiEndpoint = parser.getStr(sec, "endpoint", self.aiEndpoint)', 'self.aiEndpoint = parser.getStr(sec, "endpoint", self.aiEndpoint)\n        self.aiModel = parser.getStr(sec, "model", self.aiModel)')
config = config.replace('"endpoint": self.aiEndpoint,', '"endpoint": self.aiEndpoint,\n            "model": self.aiModel,')

with open("novelwriter/config.py", "w") as f:
    f.write(config)

with open("novelwriter/dialogs/preferences.py", "r") as f:
    prefs = f.read()

model_ui = """        # Model Selection
        modelLayout = QHBoxLayout()
        self.aiModelCombo = NComboBox(self)
        self.aiModelCombo.setMinimumWidth(200)
        self.aiModelCombo.addItem(CONFIG.aiModel)
        self.aiModelCombo.setCurrentText(CONFIG.aiModel)
        
        self.refreshModelsBtn = QPushButton("Refresh", self)
        self.refreshModelsBtn.clicked.connect(self._refreshAiModels)
        
        modelLayout.addWidget(self.aiModelCombo, 1)
        modelLayout.addWidget(self.refreshModelsBtn)
        
        modelWidget = QWidget(self)
        modelWidget.setLayout(modelLayout)
        modelLayout.setContentsMargins(0, 0, 0, 0)
        
        self.mainForm.addRow(
            self.tr("Model"),
            modelWidget,
            self.tr("Query the endpoint and select a model."),
        )
"""
prefs = prefs.replace('        # Context Size', model_ui + '\n        # Context Size')

prefs = prefs.replace('CONFIG.aiEndpoint = self.aiEndpoint.text()', 'CONFIG.aiEndpoint = self.aiEndpoint.text()\n        CONFIG.aiModel = self.aiModelCombo.currentText()')

# Add the slot
slot_code = """    @pyqtSlot()
    def _refreshAiModels(self) -> None:
        import requests
        endpoint = self.aiEndpoint.text().strip().rstrip("/")
        if not endpoint:
            return
        try:
            r = requests.get(f"{endpoint}/v1/models", timeout=3)
            r.raise_for_status()
            data = r.json()
            self.aiModelCombo.clear()
            for m in data.get("data", []):
                self.aiModelCombo.addItem(m.get("id", ""))
            
            idx = self.aiModelCombo.findText(CONFIG.aiModel)
            if idx >= 0:
                self.aiModelCombo.setCurrentIndex(idx)
        except Exception as e:
            logger.error(f"Failed to fetch models: {e}")

    @pyqtSlot(int)
    def _sidebarClicked(self, section: int) -> None:"""
prefs = prefs.replace('''    @pyqtSlot(int)
    def _sidebarClicked(self, section: int) -> None:''', slot_code)

with open("novelwriter/dialogs/preferences.py", "w") as f:
    f.write(prefs)

with open("novelwriter/gui/ai_assistant.py", "r") as f:
    ai_dock = f.read()

payload_old = """        payload = {
            "messages": ["""
payload_new = """        payload = {
            "model": getattr(CONFIG, 'aiModel', ''),
            "messages": ["""
ai_dock = ai_dock.replace(payload_old, payload_new)

with open("novelwriter/gui/ai_assistant.py", "w") as f:
    f.write(ai_dock)

print("Patch complete")
