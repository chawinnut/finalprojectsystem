# Generated by Django 4.2.20 on 2025-05-09 17:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("authentication", "0002_customuser_role"),
    ]

    operations = [
        migrations.AddField(
            model_name="customuser",
            name="is_approved",
            field=models.BooleanField(default=False, verbose_name="ได้รับการอนุมัติ"),
        ),
    ]
