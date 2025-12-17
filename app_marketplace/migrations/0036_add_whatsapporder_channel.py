from django.db import migrations, models


def add_channel_default(apps, schema_editor):
    # Safety: ensure column exists even if previous attempts failed
    WhatsappOrder = apps.get_model('app_marketplace', 'WhatsappOrder')
    # Trigger model reload; no data migration needed since default is set
    for _ in WhatsappOrder.objects.none():
        pass


class Migration(migrations.Migration):

    dependencies = [
        ('app_marketplace', '0035_merge_channel_conflict'),
    ]

    operations = [
        migrations.AddField(
            model_name='whatsapporder',
            name='channel',
            field=models.CharField(choices=[('whatsapp', 'WhatsApp'), ('site', 'Site'), ('instagram', 'Instagram'), ('store', 'Loja Física'), ('other', 'Outro')], db_index=True, default='whatsapp', max_length=20),
        ),
        migrations.RunPython(add_channel_default, reverse_code=migrations.RunPython.noop),
    ]

