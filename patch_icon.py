import glob
import os
os.chdir("/home/ab/workspaces/novelWriter")
svg = '<svg xmlns="http://www.w3.org/2000/svg" width="128" height="128" viewBox="0 0 24 24" fill="none" stroke="#000000" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M8 21h8a2 2 0 0 0 2-2v-8a2 2 0 0 0-2-2H8a2 2 0 0 0-2 2v8a2 2 0 0 0 2 2z"/><path d="M12 5V2"/><path d="M12 22v-3"/><path d="M5 12H2"/><path d="M22 12h-3"/><path d="M16 5V2"/><path d="M16 22v-3"/><path d="M8 5V2"/><path d="M8 22v-3"/><path d="M5 8H2"/><path d="M22 8h-3"/><path d="M5 16H2"/><path d="M22 16h-3"/><path d="M9 16l1.5-4 1.5 4"/><path d="M10 14h2"/><path d="M14 12v4"/></svg>'

icons_dir = "novelwriter/assets/icons"
for filename in glob.glob(os.path.join(icons_dir, "*.icons")):
    with open(filename, "a") as f:
        f.write(f"\nicon:ai_assistant      = {svg}\n")

print("Icons patched.")
