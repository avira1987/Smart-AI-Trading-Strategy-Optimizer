import os
import django
from pprint import pprint

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from core.models import APIConfiguration  # noqa: E402


def main():
    data = list(
        APIConfiguration.objects.values(
            "id", "provider", "user__username", "is_active", "api_key"
        )
    )
    pprint(data)
    print(f"Total: {len(data)}")


if __name__ == "__main__":
    main()

