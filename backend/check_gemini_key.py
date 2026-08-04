"""Report Gemini API key status without printing secret values."""
import os

import env_loader  # noqa: F401

PLACEHOLDER = "your_gemini_api_key_here"
key = os.getenv("GEMINI_API_KEY", "").strip()
model = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")

print(f".env path: {env_loader.ENV_PATH}")
print(f".env exists: {env_loader.ENV_PATH.is_file()}")
print(f"GEMINI_MODEL: {model}")

if not key:
    print("GEMINI_API_KEY: MISSING (empty or not set)")
elif key == PLACEHOLDER:
    print("GEMINI_API_KEY: PLACEHOLDER (replace with a real key in backend/.env)")
else:
    # AI Studio keys start with "AIza"; newer Google Cloud keys start with "AQ."
    print(f"GEMINI_API_KEY: SET ({key[:4]}...{key[-4:]}, length {len(key)})")
