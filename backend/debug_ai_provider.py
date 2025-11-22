import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from ai_module.provider_manager import get_provider_manager  # noqa: E402


def main():
    manager = get_provider_manager()
    print("Providers:", list(manager.providers.keys()))
    openai = manager.providers.get("openai")
    if openai:
        print("OpenAI available:", openai.is_available())
        print("OpenAI key:", bool(openai.get_api_key()))
    else:
        print("OpenAI provider missing")

    gemini = manager.providers.get("gemini")
    if gemini:
        print("Gemini available:", gemini.is_available())
    else:
        print("Gemini provider missing")


if __name__ == "__main__":
    main()

