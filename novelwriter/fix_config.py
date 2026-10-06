with open("novelwriter/config.py", "r") as f:
    lines = f.readlines()

new_lines = []
skip = False
for i, line in enumerate(lines):
    if skip:
        if "self.vimMode)" in line:
            skip = False
            new_lines.append('        self.vimMode = parser.getBool(sec, "vimMode", self.vimMode)\n\n')
            new_lines.append('        sec = "AI"\n')
            new_lines.append('        self.aiEnabled = parser.getBool(sec, "enabled", self.aiEnabled)\n')
            new_lines.append('        self.aiEnginePath = parser.getStr(sec, "enginePath", self.aiEnginePath)\n')
            new_lines.append('        self.aiModelPath = parser.getStr(sec, "modelPath", self.aiModelPath)\n')
            new_lines.append('        self.aiContextSize = parser.getInt(sec, "contextSize", self.aiContextSize)\n')
            new_lines.append('        self.aiTemperature = parser.getFloat(sec, "temperature", self.aiTemperature)\n')
        continue
    
    if "self.vimMode = parser.getBool(sec, \"vimMode\"," in line:
        skip = True
    else:
        new_lines.append(line)

with open("novelwriter/config.py", "w") as f:
    f.writelines(new_lines)
