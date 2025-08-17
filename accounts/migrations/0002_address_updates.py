from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='address',
            options={'ordering': ['-is_default', '-created_at'], 'verbose_name': 'Address', 'verbose_name_plural': 'Addresses'},
        ),
        migrations.AddField(
            model_name='address',
            name='area',
            field=models.CharField(default='', help_text='Locality/Area name', max_length=100),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='address',
            name='is_active',
            field=models.BooleanField(default=True),
        ),
    ]