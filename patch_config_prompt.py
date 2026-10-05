import os
os.chdir("/home/ab/workspaces/novelWriter")
with open("novelwriter/config.py", "r") as f:
    content = f.read()

content = content.replace('"aiTemperature",', '"aiTemperature",\n        "aiSystemPrompt",')
content = content.replace('self.aiTemperature = 0.7', 'self.aiTemperature = 0.7\n        self.aiSystemPrompt = ""')
content = content.replace('parser.getFloat(sec, "temperature", self.aiTemperature)', 'parser.getFloat(sec, "temperature", self.aiTemperature)\n        self.aiSystemPrompt = parser.getStr(sec, "systemPrompt", self.aiSystemPrompt)')
content = content.replace('"temperature": self.aiTemperature,', '"temperature": self.aiTemperature,\n            "systemPrompt": self.aiSystemPrompt,')

with open("novelwriter/config.py", "w") as f:
    f.write(content)
