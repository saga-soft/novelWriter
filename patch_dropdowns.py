import os

with open("novelwriter/gui/ai_assistant.py", "r") as f:
    content = f.read()

# Add view() minimum widths to the comboboxes
role_str = """        self.roleCombo.currentTextChanged.connect(self.changeRole)"""
role_new = """        self.roleCombo.view().setMinimumWidth(200)
        self.roleCombo.currentTextChanged.connect(self.changeRole)"""

prov_str = """        self.providerCombo.currentTextChanged.connect(self.changeProvider)"""
prov_new = """        self.providerCombo.view().setMinimumWidth(250)
        self.providerCombo.currentTextChanged.connect(self.changeProvider)"""

model_str = """        self.modelCombo.currentTextChanged.connect(self.changeModel)"""
model_new = """        self.modelCombo.view().setMinimumWidth(300)
        self.modelCombo.currentTextChanged.connect(self.changeModel)"""

content = content.replace(role_str, role_new).replace(prov_str, prov_new).replace(model_str, model_new)

with open("novelwriter/gui/ai_assistant.py", "w") as f:
    f.write(content)

print("Dropdowns patched.")
