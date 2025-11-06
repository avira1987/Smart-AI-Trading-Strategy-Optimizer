from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_alter_apiconfiguration_unique_together'),
    ]

    operations = [
        migrations.AddField(
            model_name='result',
            name='description',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='result',
            name='trades_details',
            field=models.JSONField(blank=True, default=list),
        ),
    ]


