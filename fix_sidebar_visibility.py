with open("novelwriter/gui/sidebar.py", "r") as f:
    content = f.read()

# Add a check to updateTheme
update_str = "self.tbSettings.refreshTheme()"
update_replacement = update_str + "\\n            self.tbAI.setVisible(CONFIG.aiEnabled)"
content = content.replace(update_str, update_replacement)

with open("novelwriter/gui/sidebar.py", "w") as f:
    f.write(content)

