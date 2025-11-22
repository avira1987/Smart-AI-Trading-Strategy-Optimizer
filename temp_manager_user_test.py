import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

django.setup()

from django.contrib.auth import get_user_model

from ai_module.provider_manager import get_provider_manager

def main():
    user = get_user_model().objects.get(pk=1)
    manager = get_provider_manager(user=user)
    result = manager.generate(
        'Respond with {"status":"ok"}',
        {"temperature": 0.1, "max_output_tokens": 64},
        metadata={"use_json_response_format": True},
    )
    print("success", result.success)
    print("error", result.error)
    print("text", result.text)
    print(
        "attempts",
        [(a.provider, a.success, a.error, a.status_code) for a in result.attempts],
    )


if __name__ == "__main__":
    main()

