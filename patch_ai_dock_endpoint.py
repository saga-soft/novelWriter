import os
os.chdir("/home/ab/workspaces/novelWriter")

with open("novelwriter/gui/ai_assistant.py", "r") as f:
    ai_dock = f.read()

# Fix the /v1/chat/completions double /v1
ai_dock = ai_dock.replace('url = f"{base_url}/v1/chat/completions"', 'url = f"{base_url}/chat/completions" if base_url.endswith("/v1") else f"{base_url}/v1/chat/completions"')

with open("novelwriter/gui/ai_assistant.py", "w") as f:
    f.write(ai_dock)

