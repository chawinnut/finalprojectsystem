# Generated by Django 4.2.20 on 2025-05-08 07:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("database_subscription", "0002_remove_payment_subscription_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="databasesubscription",
            name="original_currency",
            field=models.CharField(
                blank=True,
                choices=[("USD", "USD"), ("GBP", "GBP"), ("EUR", "EUR")],
                max_length=3,
                null=True,
                verbose_name="สกุลเงินต้นทาง",
            ),
        ),
        migrations.AlterField(
            model_name="databasesubscription",
            name="subscription_status",
            field=models.CharField(
                choices=[
                    ("expired", "หมดอายุ"),
                    ("current", "กำลังบอกรับอยู่ในปัจจุบัน"),
                    ("future", "กำลังจะบอกรับในอนาคต"),
                ],
                default="current",
                max_length=20,
                verbose_name="สถานะการบอกรับ",
            ),
        ),
    ]
