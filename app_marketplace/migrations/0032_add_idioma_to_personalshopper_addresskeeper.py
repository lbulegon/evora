# Generated manually to add idioma field to PersonalShopper and AddressKeeper

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app_marketplace', '0031_produtojson'),
    ]

    operations = [
        migrations.AddField(
            model_name='personalshopper',
            name='idioma',
            field=models.CharField(
                choices=[
                    ('pt-BR', 'Português (Brasil)'),
                    ('en-US', 'English (US)'),
                    ('es-ES', 'Español (España)'),
                    ('fr-FR', 'Français'),
                    ('de-DE', 'Deutsch'),
                    ('it-IT', 'Italiano'),
                ],
                default='pt-BR',
                help_text='Idioma preferido para respostas da IA',
                max_length=10
            ),
        ),
        migrations.AddField(
            model_name='addresskeeper',
            name='idioma',
            field=models.CharField(
                choices=[
                    ('pt-BR', 'Português (Brasil)'),
                    ('en-US', 'English (US)'),
                    ('es-ES', 'Español (España)'),
                    ('fr-FR', 'Français'),
                    ('de-DE', 'Deutsch'),
                    ('it-IT', 'Italiano'),
                ],
                default='pt-BR',
                help_text='Idioma preferido para respostas da IA',
                max_length=10
            ),
        ),
    ]

