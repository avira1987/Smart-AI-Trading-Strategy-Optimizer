# Generated manually to add profit_factor field to Result model

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0046_add_model_costs_to_systemsettings'),
    ]

    operations = [
        migrations.AddField(
            model_name='result',
            name='profit_factor',
            field=models.FloatField(default=0.0, help_text='نسبت سود به ضرر (Profit Factor)'),
        ),
    ]
