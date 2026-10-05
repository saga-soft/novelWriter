import os
os.chdir("/home/ab/workspaces/novelWriter")

with open("novelwriter/dialogs/preferences.py", "r") as f:
    prefs = f.read()

# Fix the /v1/models double /v1 if endpoint already has /v1
prefs = prefs.replace('r = requests.get(f"{endpoint}/v1/models", timeout=3)', 'url = f"{endpoint}/models" if endpoint.endswith("/v1") else f"{endpoint}/v1/models"\n            r = requests.get(url, timeout=3)')

with open("novelwriter/dialogs/preferences.py", "w") as f:
    f.write(prefs)

