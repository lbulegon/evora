# Generated manually
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app_marketplace', '0037_estabelecimento_conversacontextualizada_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='personalshopper',
            name='telefone',
            field=models.CharField(blank=True, help_text='Telefone de contato', max_length=20),
        ),
    ]

