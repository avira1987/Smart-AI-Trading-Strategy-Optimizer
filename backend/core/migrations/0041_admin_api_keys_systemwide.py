from django.db import migrations
from django.db.models import Q


def make_admin_api_keys_systemwide(apps, schema_editor):
    User = apps.get_model("auth", "User")
    APIConfiguration = apps.get_model("core", "APIConfiguration")

    admin_user_ids = list(
        User.objects.filter(Q(is_staff=True) | Q(is_superuser=True)).values_list("id", flat=True)
    )

    if not admin_user_ids:
        return

    APIConfiguration.objects.filter(user_id__in=admin_user_ids).update(user=None)


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0040_add_gamification_models"),
    ]

    operations = [
        migrations.RunPython(make_admin_api_keys_systemwide, migrations.RunPython.noop),
    ]

