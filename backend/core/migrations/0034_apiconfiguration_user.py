from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('core', '0033_tradingstrategy_is_primary_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='apiconfiguration',
            name='user',
            field=models.ForeignKey(
                blank=True,
                help_text='مالک کلید API؛ اگر خالی باشد کلید سیستمی است',
                null=True,
                on_delete=models.deletion.CASCADE,
                related_name='api_configurations',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddIndex(
            model_name='apiconfiguration',
            index=models.Index(fields=['provider', 'user'], name='core_api_provider_user_idx'),
        ),
    ]

