# Generated by Django 5.1.4 on 2024-12-27 16:12

import django.core.validators
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('IDGPS', '0002_alter_sklad_sotildi_sotilmadi'),
    ]

    operations = [
        migrations.CreateModel(
            name='Bugalteriya',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('oy', models.CharField(choices=[('Yanvar', 'Yanvar'), ('Fevral', 'Fevral'), ('Mart', 'Mart'), ('Aprel', 'Aprel'), ('May', 'May'), ('Iyun', 'Iyun'), ('Iyul', 'Iyul'), ('Avgust', 'Avgust'), ('Sentabr', 'Sentabr'), ('Oktabr', 'Oktabr'), ('Noyabr', 'Noyabr'), ('Dekabr', 'Dekabr')], max_length=15)),
                ('yil', models.IntegerField(help_text="Yil 2000 va hozirgi yil orasida bo'lishi kerak.", validators=[django.core.validators.MinValueValidator(2000), django.core.validators.MaxValueValidator(2024)])),
                ('abonent_tolov', models.BooleanField(default=False)),
                ('sim_karta_tolov', models.BooleanField(default=False)),
                ('izoh', models.TextField(blank=True, null=True)),
                ('sotish', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='IDGPS.sotish')),
            ],
            options={
                'verbose_name_plural': 'Bugalteriya hisobotlari',
                'unique_together': {('sotish', 'oy', 'yil')},
            },
        ),
    ]
