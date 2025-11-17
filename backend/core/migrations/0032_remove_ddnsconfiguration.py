from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0031_alter_apiconfiguration_provider'),
    ]

    operations = [
        migrations.DeleteModel(
            name='DDNSConfiguration',
        ),
    ]

