"""Report OpenAI API key status without printing secret values."""
import os

import env_loader  # noqa: F401

PLACEHOLDER = "your_openai_api_key_here"
key = os.getenv("OPENAI_API_KEY", "").strip()
model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

print(f".env path: {env_loader.ENV_PATH}")
print(f".env exists: {env_loader.ENV_PATH.is_file()}")
print(f"OPENAI_MODEL: {model}")

if not key:
    print("OPENAI_API_KEY: MISSING (empty or not set)")
elif key == PLACEHOLDER:
    print("OPENAI_API_KEY: PLACEHOLDER (replace with a real key in backend/.env)")
elif key.startswith("sk-"):
    print(f"OPENAI_API_KEY: SET (sk-...{key[-4:]}, length {len(key)})")
else:
    print(f"OPENAI_API_KEY: SET (non-sk prefix, length {len(key)})")
