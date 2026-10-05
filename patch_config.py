import sys
import os

os.chdir("/home/ab/workspaces/novelWriter")
with open("novelwriter/config.py", "r") as f:
    content = f.read()

# 1. Add __slots__
slots_str = '"vimMode",'
slots_replacement = '"vimMode",\n        "aiEnabled",\n        "aiEnginePath",\n        "aiModelPath",\n        "aiContextSize",\n        "aiTemperature",'
content = content.replace(slots_str, slots_replacement)

# 2. Add to __init__
init_str = 'self.vimMode = False  # Enable Vim mode'
init_replacement = 'self.vimMode = False\n        self.aiEnabled = False\n        self.aiEnginePath = ""\n        self.aiModelPath = ""\n        self.aiContextSize = 8192\n        self.aiTemperature = 0.7'
content = content.replace(init_str, init_replacement)

# 3. Add to loadConfig
load_str = 'self.vimMode = parser.getBool(sec, "vimMode", self.vimMode)'
load_replacement = load_str + '\n\n        sec = "AI"\n        self.aiEnabled = parser.getBool(sec, "enabled", self.aiEnabled)\n        self.aiEnginePath = parser.getStr(sec, "enginePath", self.aiEnginePath)\n        self.aiModelPath = parser.getStr(sec, "modelPath", self.aiModelPath)\n        self.aiContextSize = parser.getInt(sec, "contextSize", self.aiContextSize)\n        self.aiTemperature = parser.getFloat(sec, "temperature", self.aiTemperature)'
content = content.replace(load_str, load_replacement)

# 4. Add to saveConfig
save_str = 'config["Sizes"] = {'
save_replacement = 'config["AI"] = {\n            "enabled": self.aiEnabled,\n            "enginePath": self.aiEnginePath,\n            "modelPath": self.aiModelPath,\n            "contextSize": self.aiContextSize,\n            "temperature": self.aiTemperature,\n        }\n\n        ' + save_str
content = content.replace(save_str, save_replacement)

with open("novelwriter/config.py", "w") as f:
    f.write(content)

print("Success")
