import os
with open("novelwriter/dialogs/preferences.py", "r") as f:
    content = f.read()

content = content.replace("                self.aiApiKeyLocal = QLineEdit(self)", "        self.aiApiKeyLocal = QLineEdit(self)")

with open("novelwriter/dialogs/preferences.py", "w") as f:
    f.write(content)
