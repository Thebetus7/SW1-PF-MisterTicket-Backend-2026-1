import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tickets', '0004_ticket_propietario_ticket_transferido_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='factura',
            name='codigo_transaccion_pasarela',
            field=models.UUIDField(
                blank=True,
                default=uuid.uuid4,
                help_text='UUID único enviado a Libélula como identificador de la deuda',
                null=True,
                unique=True,
                verbose_name='Código de transacción pasarela',
            ),
        ),
    ]
