# Generated manually to update WhatsApp models to match current models.py

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app_marketplace', '__latest__'),
        ('app_whatsapp_integration', '0001_initial'),
    ]

    operations = [
        # Adicionar campos novos ao WhatsAppContact
        migrations.AddField(
            model_name='whatsappcontact',
            name='cliente',
            field=models.ForeignKey(
                blank=True,
                help_text='Cliente vinculado',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='whatsapp_contacts',
                to='app_marketplace.cliente'
            ),
        ),
        migrations.AddField(
            model_name='whatsappcontact',
            name='shopper',
            field=models.ForeignKey(
                blank=True,
                help_text='Personal Shopper vinculado',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='whatsapp_contacts',
                to='app_marketplace.personalshopper'
            ),
        ),
        migrations.AddField(
            model_name='whatsappcontact',
            name='keeper',
            field=models.ForeignKey(
                blank=True,
                help_text='Address Keeper vinculado',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='whatsapp_contacts',
                to='app_marketplace.addresskeeper'
            ),
        ),
        migrations.AddField(
            model_name='whatsappcontact',
            name='is_verified',
            field=models.BooleanField(
                default=False,
                help_text='Contato verificado no sistema'
            ),
        ),
        migrations.AddField(
            model_name='whatsappcontact',
            name='last_message_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        # Adicionar campo phone (se não existir) - manter phone_number também por compatibilidade
        migrations.AddField(
            model_name='whatsappcontact',
            name='phone',
            field=models.CharField(
                blank=True,
                help_text='Número do WhatsApp (formato: +5511999999999)',
                max_length=20,
                null=True,
                unique=True
            ),
        ),
        # Atualizar WhatsAppMessageLog
        migrations.AddField(
            model_name='whatsappmessagelog',
            name='message_id',
            field=models.CharField(
                blank=True,
                help_text='ID único da mensagem (do provedor)',
                max_length=100,
                null=True,
                unique=True
            ),
        ),
        migrations.AddField(
            model_name='whatsappmessagelog',
            name='phone',
            field=models.CharField(
                blank=True,
                help_text='Número de telefone (backup se contact for None)',
                max_length=20,
                null=True
            ),
        ),
        migrations.AddField(
            model_name='whatsappmessagelog',
            name='content',
            field=models.TextField(
                blank=True,
                help_text='Conteúdo da mensagem (texto ou URL de mídia)',
                null=True
            ),
        ),
        migrations.AddField(
            model_name='whatsappmessagelog',
            name='processed',
            field=models.BooleanField(
                default=False,
                help_text='Mensagem foi processada pelo sistema'
            ),
        ),
        migrations.AddField(
            model_name='whatsappmessagelog',
            name='reply_sent',
            field=models.BooleanField(
                default=False,
                help_text='Resposta foi enviada'
            ),
        ),
        migrations.AddField(
            model_name='whatsappmessagelog',
            name='reply_content',
            field=models.TextField(
                blank=True,
                help_text='Conteúdo da resposta enviada (se houver)'
            ),
        ),
        migrations.AddField(
            model_name='whatsappmessagelog',
            name='raw_payload',
            field=models.JSONField(
                blank=True,
                default=dict,
                help_text='Payload completo recebido do provedor'
            ),
        ),
        migrations.AddField(
            model_name='whatsappmessagelog',
            name='timestamp',
            field=models.DateTimeField(
                blank=True,
                help_text='Timestamp da mensagem (do WhatsApp)',
                null=True
            ),
        ),
        # Atualizar choices de MessageType e MessageDirection
        migrations.AlterField(
            model_name='whatsappmessagelog',
            name='message_type',
            field=models.CharField(
                choices=[
                    ('text', 'Texto'),
                    ('image', 'Imagem'),
                    ('video', 'Vídeo'),
                    ('audio', 'Áudio'),
                    ('document', 'Documento'),
                    ('location', 'Localização'),
                    ('contact', 'Contato'),
                    ('unknown', 'Desconhecido')
                ],
                default='text',
                help_text='Tipo de mensagem',
                max_length=20
            ),
        ),
        migrations.AlterField(
            model_name='whatsappmessagelog',
            name='direction',
            field=models.CharField(
                choices=[
                    ('inbound', 'Recebida'),
                    ('outbound', 'Enviada')
                ],
                db_index=True,
                default='inbound',
                help_text='Direção da mensagem',
                max_length=10
            ),
        ),
    ]

