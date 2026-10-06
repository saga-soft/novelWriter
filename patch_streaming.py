import os

with open("novelwriter/gui/ai_assistant.py", "r") as f:
    ai_dock = f.read()

# Fix anthropic parsing
old_anthropic_parse = """                                elif payload_format == "anthropic":
                                    if "delta" in data:
                                        content = data["delta"].get("text", "")
                                        if content:
                                            full_response += content
                                            self.newToken.emit(content)"""

new_anthropic_parse = """                                elif payload_format == "anthropic":
                                    if data.get("type") == "content_block_delta" and "delta" in data:
                                        content = data["delta"].get("text", "")
                                        if content:
                                            full_response += content
                                            self.newToken.emit(content)"""

ai_dock = ai_dock.replace(old_anthropic_parse, new_anthropic_parse)

with open("novelwriter/gui/ai_assistant.py", "w") as f:
    f.write(ai_dock)

print("Streaming patched.")
