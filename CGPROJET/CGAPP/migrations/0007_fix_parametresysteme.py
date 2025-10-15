from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):

    dependencies = [
        ('CGAPP', '0006_parametresysteme_alter_coupon_options_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='ParametreSysteme',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cle', models.CharField(max_length=100, unique=True, verbose_name='Clé')),
                ('valeur', models.TextField(verbose_name='Valeur')),
                ('description', models.TextField(blank=True, verbose_name='Description')),
                ('date_modification', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Paramètre système',
                'verbose_name_plural': 'Paramètres système',
                'ordering': ['cle'],
            },
        ),
    ]
