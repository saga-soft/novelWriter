import os
os.chdir("/home/ab/workspaces/novelWriter")
with open("novelwriter/gui/ai_assistant.py", "r") as f:
    content = f.read()

content = content.replace(
    'f"You are an AI assistant integrated into a writing app. Here is the current text the author is working on:\\n\\n---\\n{text}\\n---\\n\\nAssist the author as requested."',
    'f"{getattr(CONFIG, \'aiSystemPrompt\', \'\')}\\n\\nHere is the current text the author is working on:\\n\\n---\\n{text}\\n---\\n\\nAssist the author as requested."'
)

with open("novelwriter/gui/ai_assistant.py", "w") as f:
    f.write(content)
