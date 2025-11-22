import os

for key, value in os.environ.items():
    if key.startswith(("OPENAI", "GEMINI", "COHERE", "OPENROUTER", "TOGETHER", "DEEPINFRA", "GROQ")):
        print(f"{key}={value}")

