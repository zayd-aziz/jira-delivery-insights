import os
import sys
from dotenv import load_dotenv
import anthropic

load_dotenv()

if not os.getenv("ANTHROPIC_API_KEY"):
    print("Missing ANTHROPIC_API_KEY in .env")
    sys.exit(1)

client = anthropic.Anthropic()

message = client.messages.create(
    model="claude-haiku-4-5-20251001",
    max_tokens=50,
    messages=[{"role": "user", "content": "Reply with exactly: connection OK"}],
)

print("".join(block.text for block in message.content if block.type == "text"))
print(f"Tokens used: {message.usage.input_tokens} in, {message.usage.output_tokens} out")
