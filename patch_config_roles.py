import os
os.chdir("/home/ab/workspaces/novelWriter")
with open("novelwriter/config.py", "r") as f:
    content = f.read()

# Replace aiSystemPrompt with new role fields in __slots__
content = content.replace('"aiSystemPrompt",', '''"aiPromptCoAuthor",
        "aiPromptEditor",
        "aiPromptPublisher",
        "aiPromptReader",
        "aiActiveRole",''')

# Replace in __init__
init_old = 'self.aiSystemPrompt = ""'
init_new = '''self.aiPromptCoAuthor = "You are a creative co-author. Your goal is to help brainstorm, expand scenes, and enhance the narrative flow. Offer creative suggestions, maintain the author\\'s voice, and push the story forward organically."
        self.aiPromptEditor = "You are a professional literary editor. Focus on pacing, grammar, structural consistency, and clarity. Point out passive voice, repetitive phrasing, and offer precise rewriting suggestions to tighten the prose."
        self.aiPromptPublisher = "You are a commercial book publisher and marketer. Analyze the text for marketability, genre expectations, hook strength, and audience appeal. Provide feedback on how to make the story more commercially viable."
        self.aiPromptReader = "You are an avid reader of this genre. Provide emotional reactions, point out where you get confused or bored, and highlight your favorite moments. React as a fan experiencing the story for the first time."
        self.aiActiveRole = "Co-author"'''
content = content.replace(init_old, init_new)

# Replace in loadConfig
load_old = 'self.aiSystemPrompt = parser.getStr(sec, "systemPrompt", self.aiSystemPrompt)'
load_new = '''self.aiPromptCoAuthor = parser.getStr(sec, "promptCoAuthor", self.aiPromptCoAuthor)
        self.aiPromptEditor = parser.getStr(sec, "promptEditor", self.aiPromptEditor)
        self.aiPromptPublisher = parser.getStr(sec, "promptPublisher", self.aiPromptPublisher)
        self.aiPromptReader = parser.getStr(sec, "promptReader", self.aiPromptReader)
        self.aiActiveRole = parser.getStr(sec, "activeRole", self.aiActiveRole)'''
content = content.replace(load_old, load_new)

# Replace in saveConfig
save_old = '"systemPrompt": self.aiSystemPrompt,'
save_new = '''"promptCoAuthor": self.aiPromptCoAuthor,
            "promptEditor": self.aiPromptEditor,
            "promptPublisher": self.aiPromptPublisher,
            "promptReader": self.aiPromptReader,
            "activeRole": self.aiActiveRole,'''
content = content.replace(save_old, save_new)

with open("novelwriter/config.py", "w") as f:
    f.write(content)

